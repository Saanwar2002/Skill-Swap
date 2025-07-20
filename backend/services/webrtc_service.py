"""
WebRTC Service for Video Chat Integration
Handles WebSocket signaling for peer-to-peer video calls
"""

import json
import logging
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for WebRTC signaling"""
    
    def __init__(self):
        # Store connections: session_id -> {user_id -> websocket}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Store user sessions: user_id -> session_id
        self.user_sessions: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """Connect a user to a session"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        
        self.active_connections[session_id][user_id] = websocket
        self.user_sessions[user_id] = session_id
        
        logger.info(f"User {user_id} connected to session {session_id}")
        
        # Notify other users in the session
        await self.broadcast_to_session(session_id, {
            "type": "user_joined",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_user=user_id)
    
    def disconnect(self, user_id: str):
        """Disconnect a user"""
        session_id = self.user_sessions.get(user_id)
        if session_id and session_id in self.active_connections:
            if user_id in self.active_connections[session_id]:
                del self.active_connections[session_id][user_id]
            
            # Remove empty sessions
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        logger.info(f"User {user_id} disconnected from session {session_id}")
        
        # Notify other users in the session
        if session_id and session_id in self.active_connections:
            asyncio.create_task(self.broadcast_to_session(session_id, {
                "type": "user_left",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def send_personal_message(self, message: dict, target_user_id: str):
        """Send message to specific user"""
        session_id = self.user_sessions.get(target_user_id)
        if session_id and session_id in self.active_connections:
            if target_user_id in self.active_connections[session_id]:
                websocket = self.active_connections[session_id][target_user_id]
                try:
                    await websocket.send_text(json.dumps(message))
                    logger.debug(f"Sent message to user {target_user_id}: {message['type']}")
                except Exception as e:
                    logger.error(f"Error sending message to {target_user_id}: {e}")
                    self.disconnect(target_user_id)
    
    async def broadcast_to_session(self, session_id: str, message: dict, exclude_user: Optional[str] = None):
        """Broadcast message to all users in a session"""
        if session_id in self.active_connections:
            disconnected_users = []
            
            for user_id, websocket in self.active_connections[session_id].items():
                if exclude_user and user_id == exclude_user:
                    continue
                
                try:
                    await websocket.send_text(json.dumps(message))
                    logger.debug(f"Broadcasted to user {user_id}: {message['type']}")
                except Exception as e:
                    logger.error(f"Error broadcasting to {user_id}: {e}")
                    disconnected_users.append(user_id)
            
            # Clean up disconnected users
            for user_id in disconnected_users:
                self.disconnect(user_id)
    
    def get_session_users(self, session_id: str) -> List[str]:
        """Get list of users in a session"""
        if session_id in self.active_connections:
            return list(self.active_connections[session_id].keys())
        return []


class WebRTCService:
    """Service for WebRTC configuration and management"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
    
    def get_ice_servers(self) -> List[dict]:
        """Get ICE servers configuration (STUN/TURN)"""
        ice_servers = [
            # Google's public STUN servers (free)
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"},
        ]
        
        # Add TURN server if configured
        turn_server = os.getenv("TURN_SERVER")
        turn_username = os.getenv("TURN_USERNAME")
        turn_password = os.getenv("TURN_PASSWORD")
        
        if turn_server and turn_username and turn_password:
            ice_servers.append({
                "urls": f"turn:{turn_server}",
                "username": turn_username,
                "credential": turn_password
            })
            logger.info("TURN server configured")
        else:
            logger.info("Using STUN servers only (TURN server not configured)")
        
        return ice_servers
    
    async def handle_signaling_message(self, websocket: WebSocket, user_id: str, message: dict):
        """Handle WebRTC signaling messages"""
        message_type = message.get("type")
        target_user_id = message.get("target_user_id")
        
        if not target_user_id:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "target_user_id is required"
            }))
            return
        
        # Forward signaling message to target user
        signaling_message = {
            "type": message_type,
            "from_user_id": user_id,
            "data": message.get("data"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.send_personal_message(
            signaling_message, 
            target_user_id
        )
        
        logger.debug(f"Forwarded {message_type} from {user_id} to {target_user_id}")
    
    async def get_session_info(self, session_id: str) -> dict:
        """Get information about active session"""
        users = self.connection_manager.get_session_users(session_id)
        return {
            "session_id": session_id,
            "active_users": users,
            "user_count": len(users),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global WebRTC service instance
webrtc_service = WebRTCService()

import asyncio