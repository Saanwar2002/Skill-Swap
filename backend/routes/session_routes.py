from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from models import Session, SessionStatus, User, SessionCreate, SessionUpdate
from services.session_service import SessionService
from auth import AuthService
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

def create_session_router(db: AsyncIOMotorClient) -> APIRouter:
    router = APIRouter(prefix="/sessions", tags=["Sessions"])
    session_service = SessionService(db)
    auth_service = AuthService(db)
    
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """Get current authenticated user"""
        try:
            token = credentials.credentials
            return await auth_service.get_current_user(token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    @router.post("/", response_model=Session)
    async def create_session(
        session_data: SessionCreate,
        current_user: User = Depends(get_current_user)
    ):
        """Create a new session"""
        try:
            # Validate that current user is either teacher or learner
            if current_user.id != session_data.teacher_id and current_user.id != session_data.learner_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only create sessions where you are a participant"
                )
            
            # Convert session data to dict
            session_dict = session_data.dict()
            
            # Create session
            session = await session_service.create_session(
                teacher_id=session_data.teacher_id,
                learner_id=session_data.learner_id,
                session_data=session_dict
            )
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not create session"
                )
            
            return session
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Create session error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create session"
            )
    
    @router.get("/", response_model=List[Session])
    async def get_my_sessions(
        role: str = Query("all", description="Filter by role: all, teacher, learner"),
        status: str = Query("all", description="Filter by status: all, scheduled, in_progress, completed, cancelled"),
        limit: int = Query(50, description="Maximum number of sessions to return"),
        current_user: User = Depends(get_current_user)
    ):
        """Get current user's sessions"""
        try:
            sessions = await session_service.get_user_sessions(
                user_id=current_user.id,
                role=role,
                status=status,
                limit=limit
            )
            return sessions
            
        except Exception as e:
            logger.error(f"Get my sessions error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve sessions"
            )
    
    @router.get("/upcoming", response_model=List[Session])
    async def get_upcoming_sessions(
        limit: int = Query(20, description="Maximum number of sessions to return"),
        current_user: User = Depends(get_current_user)
    ):
        """Get upcoming sessions for current user"""
        try:
            sessions = await session_service.get_upcoming_sessions(
                user_id=current_user.id,
                limit=limit
            )
            return sessions
            
        except Exception as e:
            logger.error(f"Get upcoming sessions error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve upcoming sessions"
            )
    
    @router.get("/{session_id}", response_model=Session)
    async def get_session(
        session_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Get session by ID"""
        try:
            session = await session_service.get_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            # Check if user is participant
            if session.teacher_id != current_user.id and session.learner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view sessions where you are a participant"
                )
            
            return session
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get session error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve session"
            )
    
    @router.put("/{session_id}", response_model=Session)
    async def update_session(
        session_id: str,
        update_data: SessionUpdate,
        current_user: User = Depends(get_current_user)
    ):
        """Update session"""
        try:
            session = await session_service.get_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            # Check if user is participant
            if session.teacher_id != current_user.id and session.learner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update sessions where you are a participant"
                )
            
            # Update session
            updated_session = await session_service.update_session(
                session_id=session_id,
                update_data=update_data.dict(exclude_unset=True)
            )
            
            if not updated_session:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not update session"
                )
            
            return updated_session
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Update session error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not update session"
            )
    
    @router.post("/{session_id}/cancel")
    async def cancel_session(
        session_id: str,
        reason: Optional[str] = None,
        current_user: User = Depends(get_current_user)
    ):
        """Cancel a session"""
        try:
            success = await session_service.cancel_session(
                session_id=session_id,
                user_id=current_user.id,
                reason=reason
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not cancel session"
                )
            
            return {"message": "Session cancelled successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Cancel session error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not cancel session"
            )
    
    @router.post("/{session_id}/start")
    async def start_session(
        session_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Start a session"""
        try:
            success = await session_service.start_session(
                session_id=session_id,
                user_id=current_user.id
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not start session"
                )
            
            return {"message": "Session started successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Start session error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not start session"
            )
    
    @router.post("/{session_id}/end")
    async def end_session(
        session_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """End a session"""
        try:
            success = await session_service.end_session(
                session_id=session_id,
                user_id=current_user.id
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not end session"
                )
            
            return {"message": "Session ended successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"End session error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not end session"
            )
    
    @router.post("/{session_id}/feedback")
    async def submit_feedback(
        session_id: str,
        rating: float = Query(..., ge=1, le=5, description="Rating from 1 to 5"),
        feedback: str = Query(..., description="Feedback text"),
        current_user: User = Depends(get_current_user)
    ):
        """Submit session feedback and rating"""
        try:
            success = await session_service.submit_session_feedback(
                session_id=session_id,
                user_id=current_user.id,
                rating=rating,
                feedback=feedback
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not submit feedback"
                )
            
            return {"message": "Feedback submitted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Submit feedback error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not submit feedback"
            )
    
    @router.get("/user/{user_id}/statistics", response_model=Dict[str, Any])
    async def get_user_session_statistics(
        user_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Get session statistics for a user"""
        try:
            # Users can only view their own statistics unless they're viewing a public profile
            if user_id != current_user.id:
                # In a real app, you might want to check if the profile is public
                # For now, we'll allow viewing other user's statistics
                pass
            
            stats = await session_service.get_session_statistics(user_id)
            return stats
            
        except Exception as e:
            logger.error(f"Get user statistics error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve statistics"
            )
    
    @router.get("/user/{user_id}/availability")
    async def get_user_availability(
        user_id: str,
        date: datetime = Query(..., description="Date to check availability"),
        skill_id: Optional[str] = Query(None, description="Skill ID filter"),
        current_user: User = Depends(get_current_user)
    ):
        """Get available time slots for a user"""
        try:
            slots = await session_service.get_available_time_slots(
                teacher_id=user_id,
                date=date,
                skill_id=skill_id
            )
            
            return {"available_slots": slots}
            
        except Exception as e:
            logger.error(f"Get availability error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve availability"
            )
    
    @router.get("/search", response_model=List[Session])
    async def search_sessions(
        query: Optional[str] = Query(None, description="Search query"),
        status: Optional[str] = Query(None, description="Filter by status"),
        skill_id: Optional[str] = Query(None, description="Filter by skill ID"),
        teacher_id: Optional[str] = Query(None, description="Filter by teacher ID"),
        learner_id: Optional[str] = Query(None, description="Filter by learner ID"),
        date_from: Optional[datetime] = Query(None, description="Filter sessions from date"),
        date_to: Optional[datetime] = Query(None, description="Filter sessions to date"),
        limit: int = Query(20, description="Maximum number of results"),
        current_user: User = Depends(get_current_user)
    ):
        """Search sessions"""
        try:
            filters = {}
            if status:
                filters["status"] = status
            if skill_id:
                filters["skill_id"] = skill_id
            if teacher_id:
                filters["teacher_id"] = teacher_id
            if learner_id:
                filters["learner_id"] = learner_id
            if date_from:
                filters["date_from"] = date_from
            if date_to:
                filters["date_to"] = date_to
            
            sessions = await session_service.search_sessions(
                query=query or "",
                filters=filters,
                limit=limit
            )
            
            # Filter to only show sessions where current user is a participant
            user_sessions = [
                session for session in sessions
                if session.teacher_id == current_user.id or session.learner_id == current_user.id
            ]
            
            return user_sessions
            
        except Exception as e:
            logger.error(f"Search sessions error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not search sessions"
            )
    
    return router