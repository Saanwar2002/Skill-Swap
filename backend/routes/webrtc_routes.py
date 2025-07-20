"""
WebRTC WebSocket Routes
Handles WebSocket connections for video call signaling
"""

import json
import logging
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from services.webrtc_service import webrtc_service
from auth import AuthService
from services.session_service import SessionService
from jose import jwt, JWTError
import os

logger = logging.getLogger(__name__)

security = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "fallback-secret-key")
ALGORITHM = "HS256"


def create_webrtc_router(db) -> APIRouter:
    router = APIRouter(prefix="/webrtc", tags=["webrtc"])
    auth_service = AuthService(db)
    session_service = SessionService(db)

    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current user from JWT token"""
        try:
            token = credentials.credentials
            user = await auth_service.get_current_user(token)
            return user.dict()
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )

    async def authenticate_websocket_token(token: str) -> str:
        """Authenticate WebSocket connection using JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise JWTError("Invalid token payload")
            return user_id
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

    @router.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        """WebSocket endpoint for WebRTC signaling"""
        user_id = None
        
        try:
            # Get token from query parameters
            token = websocket.query_params.get("token")
            if not token:
                await websocket.close(code=1008, reason="Authentication token required")
                return
            
            # Authenticate user
            try:
                user_id = await authenticate_websocket_token(token)
            except HTTPException:
                await websocket.close(code=1008, reason="Invalid authentication token")
                return
            
            # Verify user has access to the session
            try:
                session = await session_service.get_session(session_id)
                if not session:
                    await websocket.close(code=1008, reason="Session not found")
                    return
                
                # Check if user is participant
                if session.teacher_id != user_id and session.learner_id != user_id:
                    await websocket.close(code=1008, reason="Access denied")
                    return
            except Exception as e:
                logger.error(f"Error verifying session access: {e}")
                await websocket.close(code=1008, reason="Session verification failed")
                return
            
            # Connect to WebRTC signaling
            await webrtc_service.connection_manager.connect(websocket, session_id, user_id)
            
            # Send initial configuration
            await websocket.send_text(json.dumps({
                "type": "connected",
                "session_id": session_id,
                "user_id": user_id,
                "ice_servers": webrtc_service.get_ice_servers()
            }))
            
            # Handle messages
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    if message_type in ["offer", "answer", "ice-candidate"]:
                        await webrtc_service.handle_signaling_message(websocket, user_id, message)
                    elif message_type.startswith("whiteboard:"):
                        await webrtc_service.handle_signaling_message(websocket, user_id, message)
                    elif message_type == "heartbeat":
                        await websocket.send_text(json.dumps({"type": "heartbeat-ack"}))
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received from {user_id}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                except Exception as e:
                    logger.error(f"Error handling message from {user_id}: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Message processing failed"
                    }))
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket connection: {e}")
        finally:
            if user_id:
                webrtc_service.connection_manager.disconnect(user_id)

    @router.get("/config")
    async def get_webrtc_config(current_user: dict = Depends(get_current_user)):
        """Get WebRTC configuration for client"""
        return {
            "ice_servers": webrtc_service.get_ice_servers(),
            "user_id": current_user["id"]
        }

    @router.get("/session/{session_id}/info")
    async def get_session_info(
        session_id: str, 
        current_user: dict = Depends(get_current_user)
    ):
        """Get information about active WebRTC session"""
        try:
            # Verify user has access to the session
            session = await session_service.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Check if user is participant
            if session.teacher_id != current_user["id"] and session.learner_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            session_info = await webrtc_service.get_session_info(session_id)
            return session_info
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            raise HTTPException(status_code=500, detail="Failed to get session information")

    @router.post("/session/{session_id}/start-call")
    async def start_video_call(
        session_id: str, 
        current_user: dict = Depends(get_current_user)
    ):
        """Start a video call for a session"""
        try:
            # Verify user has access to the session
            session = await session_service.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Check if user is participant
            if session.teacher_id != current_user["id"] and session.learner_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Check if session is in correct status for video call
            if session.status != "in_progress":
                raise HTTPException(
                    status_code=400, 
                    detail="Video call can only be started for sessions in progress"
                )
            
            # Notify all users in the session about the call start
            await webrtc_service.connection_manager.broadcast_to_session(session_id, {
                "type": "call_started",
                "initiated_by": current_user["id"],
                "session_id": session_id
            })
            
            return {
                "message": "Video call initiated",
                "session_id": session_id,
                "websocket_url": f"/api/webrtc/ws/{session_id}"
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error starting video call: {e}")
            raise HTTPException(status_code=500, detail="Failed to start video call")

    @router.post("/session/{session_id}/end-call")
    async def end_video_call(
        session_id: str, 
        current_user: dict = Depends(get_current_user)
    ):
        """End a video call for a session"""
        try:
            # Verify user has access to the session
            session = await session_service.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Check if user is participant
            if session.teacher_id != current_user["id"] and session.learner_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Notify all users in the session about the call end
            await webrtc_service.connection_manager.broadcast_to_session(session_id, {
                "type": "call_ended",
                "ended_by": current_user["id"],
                "session_id": session_id
            })
            
            return {
                "message": "Video call ended",
                "session_id": session_id
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error ending video call: {e}")
            raise HTTPException(status_code=500, detail="Failed to end video call")

    return router


# For backward compatibility, create a router instance
# This will be removed once server.py is updated
router = APIRouter(prefix="/api/webrtc", tags=["webrtc"])