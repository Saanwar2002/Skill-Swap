from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from typing import List, Optional
import logging
from datetime import datetime
import json

from auth import get_current_user
from models import Message, Conversation, MessageCreate, User, MessageType
from services.message_service import MessageService
from services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

def create_message_router(db):
    router = APIRouter(prefix="/messages", tags=["messages"])
    message_service = MessageService(db)
    
    # WebSocket endpoint for real-time messaging
    @router.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        """WebSocket endpoint for real-time messaging"""
        try:
            # Connect the WebSocket
            connected = await websocket_manager.connect(websocket, user_id)
            if not connected:
                await websocket.close(code=1000, reason="Failed to establish connection")
                return
            
            # Listen for messages
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await websocket_manager.handle_message(user_id, message)
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user: {user_id}")
            except Exception as e:
                logger.error(f"Error in WebSocket connection for user {user_id}: {str(e)}")
            finally:
                await websocket_manager.disconnect(user_id)
                
        except Exception as e:
            logger.error(f"WebSocket connection error for user {user_id}: {str(e)}")
            await websocket.close(code=1000, reason="Internal server error")
    
    # REST API endpoints
    @router.get("/conversations", response_model=List[Conversation])
    async def get_user_conversations(current_user: User = Depends(get_current_user)):
        """Get all conversations for the current user"""
        try:
            conversations = await message_service.get_user_conversations(current_user.id)
            return conversations
        except Exception as e:
            logger.error(f"Error getting conversations for user {current_user.id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get conversations")
    
    @router.post("/conversations", response_model=Conversation)
    async def create_conversation(
        participants: List[str],
        session_id: Optional[str] = None,
        current_user: User = Depends(get_current_user)
    ):
        """Create a new conversation"""
        try:
            # Ensure current user is in participants
            if current_user.id not in participants:
                participants.append(current_user.id)
            
            conversation = await message_service.create_conversation(participants, session_id)
            return conversation
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create conversation")
    
    @router.get("/conversations/{conversation_id}", response_model=Conversation)
    async def get_conversation(
        conversation_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Get a specific conversation"""
        try:
            conversation = await message_service.get_conversation(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Check if user is participant
            if current_user.id not in conversation.participants:
                raise HTTPException(status_code=403, detail="Access denied")
            
            return conversation
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get conversation")
    
    @router.get("/conversations/{conversation_id}/messages", response_model=List[Message])
    async def get_conversation_messages(
        conversation_id: str,
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        current_user: User = Depends(get_current_user)
    ):
        """Get messages for a conversation"""
        try:
            # Verify user is participant
            conversation = await message_service.get_conversation(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            if current_user.id not in conversation.participants:
                raise HTTPException(status_code=403, detail="Access denied")
            
            messages = await message_service.get_conversation_messages(conversation_id, limit, offset)
            return messages
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get messages")
    
    @router.post("/send", response_model=Message)
    async def send_message(
        message_data: MessageCreate,
        current_user: User = Depends(get_current_user)
    ):
        """Send a new message"""
        try:
            # Send message
            message = await message_service.send_message(current_user.id, message_data)
            
            # Broadcast to WebSocket clients
            participants = [current_user.id, message_data.recipient_id]
            await websocket_manager.broadcast_to_conversation(
                message.conversation_id,
                participants,
                {
                    "type": "new_message",
                    "message": message.dict(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return message
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to send message")
    
    @router.put("/messages/{message_id}/read")
    async def mark_message_as_read(
        message_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Mark a message as read"""
        try:
            success = await message_service.mark_message_as_read(message_id, current_user.id)
            if not success:
                raise HTTPException(status_code=404, detail="Message not found or already read")
            
            return {"message": "Message marked as read"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to mark message as read")
    
    @router.put("/conversations/{conversation_id}/read")
    async def mark_conversation_as_read(
        conversation_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Mark all messages in a conversation as read"""
        try:
            # Verify user is participant
            conversation = await message_service.get_conversation(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            if current_user.id not in conversation.participants:
                raise HTTPException(status_code=403, detail="Access denied")
            
            success = await message_service.mark_conversation_as_read(conversation_id, current_user.id)
            
            # Notify other participants
            await websocket_manager.notify_message_read(
                conversation_id,
                None,  # All messages
                current_user.id,
                conversation.participants
            )
            
            return {"message": "Conversation marked as read"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error marking conversation as read: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to mark conversation as read")
    
    @router.get("/unread-count")
    async def get_unread_count(current_user: User = Depends(get_current_user)):
        """Get count of unread messages for current user"""
        try:
            count = await message_service.get_unread_message_count(current_user.id)
            return {"unread_count": count}
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get unread count")
    
    @router.delete("/messages/{message_id}")
    async def delete_message(
        message_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Delete a message (only sender can delete)"""
        try:
            success = await message_service.delete_message(message_id, current_user.id)
            if not success:
                raise HTTPException(status_code=404, detail="Message not found or access denied")
            
            return {"message": "Message deleted"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting message: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete message")
    
    @router.put("/messages/{message_id}/edit")
    async def edit_message(
        message_id: str,
        new_content: str,
        current_user: User = Depends(get_current_user)
    ):
        """Edit a message (only sender can edit)"""
        try:
            success = await message_service.edit_message(message_id, current_user.id, new_content)
            if not success:
                raise HTTPException(status_code=404, detail="Message not found or access denied")
            
            return {"message": "Message edited"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error editing message: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to edit message")
    
    @router.get("/search")
    async def search_messages(
        query: str = Query(..., min_length=1),
        limit: int = Query(20, ge=1, le=50),
        current_user: User = Depends(get_current_user)
    ):
        """Search messages for the current user"""
        try:
            messages = await message_service.search_messages(current_user.id, query, limit)
            return {"messages": messages}
        except Exception as e:
            logger.error(f"Error searching messages: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to search messages")
    
    @router.get("/online-users")
    async def get_online_users(current_user: User = Depends(get_current_user)):
        """Get list of online users"""
        try:
            online_users = websocket_manager.get_online_users()
            return {"online_users": online_users}
        except Exception as e:
            logger.error(f"Error getting online users: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get online users")
    
    return router