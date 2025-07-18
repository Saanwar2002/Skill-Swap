import logging
from typing import List, Optional, Dict
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import Message, Conversation, MessageCreate, MessageType
from bson import ObjectId
import uuid

logger = logging.getLogger(__name__)

class MessageService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.messages_collection = db.messages
        self.conversations_collection = db.conversations
        
    async def create_conversation(self, participants: List[str], session_id: Optional[str] = None) -> Conversation:
        """Create a new conversation between participants"""
        try:
            # Check if conversation already exists between these participants
            existing_conversation = await self.conversations_collection.find_one({
                "participants": {"$all": participants, "$size": len(participants)},
                "is_active": True
            })
            
            if existing_conversation:
                return Conversation(**existing_conversation)
            
            # Create new conversation
            conversation = Conversation(
                participants=sorted(participants),  # Sort for consistency
                session_id=session_id
            )
            
            await self.conversations_collection.insert_one(conversation.dict())
            logger.info(f"Created new conversation: {conversation.id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        try:
            conversation_data = await self.conversations_collection.find_one({"id": conversation_id})
            if conversation_data:
                return Conversation(**conversation_data)
            return None
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return None
    
    async def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """Get all conversations for a user"""
        try:
            conversations = await self.conversations_collection.find({
                "participants": user_id,
                "is_active": True
            }).sort("last_message_at", -1).to_list(100)
            
            return [Conversation(**conv) for conv in conversations]
        except Exception as e:
            logger.error(f"Error getting user conversations: {str(e)}")
            return []
    
    async def send_message(self, sender_id: str, message_data: MessageCreate) -> Message:
        """Send a new message"""
        try:
            # Get or create conversation
            participants = [sender_id, message_data.recipient_id]
            conversation = await self.create_conversation(participants, message_data.session_id)
            
            # Create message
            message = Message(
                sender_id=sender_id,
                recipient_id=message_data.recipient_id,
                session_id=message_data.session_id,
                conversation_id=conversation.id,
                content=message_data.content,
                message_type=message_data.message_type,
                file_data=message_data.file_data,
                file_name=message_data.file_name,
                file_size=len(message_data.file_data) if message_data.file_data else None,
                reply_to=message_data.reply_to
            )
            
            # Insert message
            await self.messages_collection.insert_one(message.dict())
            
            # Update conversation
            await self.conversations_collection.update_one(
                {"id": conversation.id},
                {
                    "$set": {
                        "last_message_id": message.id,
                        "last_message_at": message.created_at
                    }
                }
            )
            
            logger.info(f"Message sent from {sender_id} to {message_data.recipient_id}")
            return message
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise
    
    async def get_conversation_messages(self, conversation_id: str, limit: int = 50, offset: int = 0) -> List[Message]:
        """Get messages for a conversation"""
        try:
            messages = await self.messages_collection.find({
                "conversation_id": conversation_id
            }).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
            
            # Reverse to get chronological order
            messages.reverse()
            return [Message(**msg) for msg in messages]
            
        except Exception as e:
            logger.error(f"Error getting conversation messages: {str(e)}")
            return []
    
    async def mark_message_as_read(self, message_id: str, user_id: str) -> bool:
        """Mark a message as read"""
        try:
            result = await self.messages_collection.update_one(
                {"id": message_id, "recipient_id": user_id},
                {"$set": {"is_read": True, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return False
    
    async def mark_conversation_as_read(self, conversation_id: str, user_id: str) -> bool:
        """Mark all messages in a conversation as read for a user"""
        try:
            result = await self.messages_collection.update_many(
                {"conversation_id": conversation_id, "recipient_id": user_id, "is_read": False},
                {"$set": {"is_read": True, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error marking conversation as read: {str(e)}")
            return False
    
    async def get_unread_message_count(self, user_id: str) -> int:
        """Get the count of unread messages for a user"""
        try:
            count = await self.messages_collection.count_documents({
                "recipient_id": user_id,
                "is_read": False
            })
            return count
            
        except Exception as e:
            logger.error(f"Error getting unread message count: {str(e)}")
            return 0
    
    async def delete_message(self, message_id: str, user_id: str) -> bool:
        """Delete a message (only sender can delete)"""
        try:
            result = await self.messages_collection.delete_one({
                "id": message_id,
                "sender_id": user_id
            })
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting message: {str(e)}")
            return False
    
    async def edit_message(self, message_id: str, user_id: str, new_content: str) -> bool:
        """Edit a message (only sender can edit)"""
        try:
            result = await self.messages_collection.update_one(
                {"id": message_id, "sender_id": user_id},
                {
                    "$set": {
                        "content": new_content,
                        "is_edited": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error editing message: {str(e)}")
            return False
    
    async def search_messages(self, user_id: str, query: str, limit: int = 20) -> List[Message]:
        """Search messages for a user"""
        try:
            messages = await self.messages_collection.find({
                "$and": [
                    {"$or": [{"sender_id": user_id}, {"recipient_id": user_id}]},
                    {"content": {"$regex": query, "$options": "i"}}
                ]
            }).sort("created_at", -1).limit(limit).to_list(limit)
            
            return [Message(**msg) for msg in messages]
            
        except Exception as e:
            logger.error(f"Error searching messages: {str(e)}")
            return []