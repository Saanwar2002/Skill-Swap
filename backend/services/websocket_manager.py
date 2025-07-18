import logging
import json
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class WebSocketConnection:
    def __init__(self, websocket: WebSocket, user_id: str):
        self.websocket = websocket
        self.user_id = user_id
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()

class WebSocketManager:
    def __init__(self):
        # Store active connections: user_id -> WebSocketConnection
        self.active_connections: Dict[str, WebSocketConnection] = {}
        # Store user conversations for broadcasting
        self.user_conversations: Dict[str, List[str]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket for a user"""
        try:
            await websocket.accept()
            
            # Close existing connection if any
            if user_id in self.active_connections:
                await self.disconnect(user_id)
            
            # Store new connection
            self.active_connections[user_id] = WebSocketConnection(websocket, user_id)
            
            logger.info(f"WebSocket connected for user: {user_id}")
            
            # Send connection confirmation
            await self.send_to_user(user_id, {
                "type": "connection_established",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket for user {user_id}: {str(e)}")
            return False
    
    async def disconnect(self, user_id: str):
        """Disconnect a user's WebSocket"""
        try:
            if user_id in self.active_connections:
                connection = self.active_connections[user_id]
                await connection.websocket.close()
                del self.active_connections[user_id]
                
                # Clean up conversation tracking
                if user_id in self.user_conversations:
                    del self.user_conversations[user_id]
                
                logger.info(f"WebSocket disconnected for user: {user_id}")
                
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket for user {user_id}: {str(e)}")
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if a user is currently online"""
        return user_id in self.active_connections
    
    def get_online_users(self) -> List[str]:
        """Get list of all online users"""
        return list(self.active_connections.keys())
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to a specific user"""
        try:
            if user_id in self.active_connections:
                connection = self.active_connections[user_id]
                await connection.websocket.send_text(json.dumps(message))
                return True
            return False
            
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user: {user_id}")
            await self.disconnect(user_id)
            return False
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {str(e)}")
            await self.disconnect(user_id)
            return False
    
    async def broadcast_to_conversation(self, conversation_id: str, participants: List[str], message: dict):
        """Broadcast a message to all participants in a conversation"""
        successful_sends = 0
        
        for user_id in participants:
            if await self.send_to_user(user_id, {
                **message,
                "conversation_id": conversation_id
            }):
                successful_sends += 1
        
        return successful_sends
    
    async def notify_typing(self, conversation_id: str, user_id: str, participants: List[str], is_typing: bool):
        """Notify participants that a user is typing"""
        message = {
            "type": "typing_indicator",
            "conversation_id": conversation_id,
            "user_id": user_id,
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all participants except the sender
        for participant_id in participants:
            if participant_id != user_id:
                await self.send_to_user(participant_id, message)
    
    async def notify_message_read(self, conversation_id: str, message_id: str, reader_id: str, participants: List[str]):
        """Notify participants that a message was read"""
        message = {
            "type": "message_read",
            "conversation_id": conversation_id,
            "message_id": message_id,
            "reader_id": reader_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all participants except the reader
        for participant_id in participants:
            if participant_id != reader_id:
                await self.send_to_user(participant_id, message)
    
    async def notify_user_online_status(self, user_id: str, is_online: bool, notify_users: List[str] = None):
        """Notify specific users about a user's online status change"""
        message = {
            "type": "user_status_change",
            "user_id": user_id,
            "is_online": is_online,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if notify_users:
            for notify_user_id in notify_users:
                if notify_user_id != user_id:
                    await self.send_to_user(notify_user_id, message)
    
    async def handle_message(self, user_id: str, message: dict):
        """Handle incoming WebSocket message from client"""
        try:
            message_type = message.get("type")
            
            if message_type == "ping":
                # Update last ping time
                if user_id in self.active_connections:
                    self.active_connections[user_id].last_ping = datetime.utcnow()
                
                # Send pong response
                await self.send_to_user(user_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "typing_start":
                conversation_id = message.get("conversation_id")
                participants = message.get("participants", [])
                await self.notify_typing(conversation_id, user_id, participants, True)
            
            elif message_type == "typing_stop":
                conversation_id = message.get("conversation_id")
                participants = message.get("participants", [])
                await self.notify_typing(conversation_id, user_id, participants, False)
            
            elif message_type == "mark_read":
                conversation_id = message.get("conversation_id")
                message_id = message.get("message_id")
                participants = message.get("participants", [])
                await self.notify_message_read(conversation_id, message_id, user_id, participants)
            
            else:
                logger.warning(f"Unknown message type: {message_type} from user: {user_id}")
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message from user {user_id}: {str(e)}")
    
    async def cleanup_stale_connections(self):
        """Clean up stale connections (ping timeout)"""
        try:
            current_time = datetime.utcnow()
            stale_users = []
            
            for user_id, connection in self.active_connections.items():
                # Check if last ping was more than 2 minutes ago
                if (current_time - connection.last_ping).total_seconds() > 120:
                    stale_users.append(user_id)
            
            for user_id in stale_users:
                logger.info(f"Cleaning up stale connection for user: {user_id}")
                await self.disconnect(user_id)
                
        except Exception as e:
            logger.error(f"Error cleaning up stale connections: {str(e)}")

# Create global WebSocket manager instance
websocket_manager = WebSocketManager()

# Periodic cleanup task
async def periodic_cleanup():
    """Periodically clean up stale connections"""
    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            await websocket_manager.cleanup_stale_connections()
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {str(e)}")

# Start cleanup task
asyncio.create_task(periodic_cleanup())