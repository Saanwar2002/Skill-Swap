from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any
from models import User, MatchFilters
from services.matching_service import MatchingService
from auth import AuthService
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

def create_matching_router(db: AsyncIOMotorClient) -> APIRouter:
    router = APIRouter(prefix="/matching", tags=["Matching"])
    matching_service = MatchingService(db)
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
    
    @router.post("/find", response_model=List[Dict[str, Any]])
    async def find_matches(
        filters: Optional[MatchFilters] = None,
        limit: int = Query(20, description="Maximum number of matches"),
        current_user: User = Depends(get_current_user)
    ):
        """Find AI-powered matches for current user"""
        try:
            matches = await matching_service.find_matches(current_user.id, filters, limit)
            return matches
        except Exception as e:
            logger.error(f"Find matches error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not find matches"
            )
    
    @router.get("/my-matches", response_model=List[Dict[str, Any]])
    async def get_my_matches(
        status_filter: Optional[str] = Query(None, description="Filter by match status"),
        limit: int = Query(20, description="Maximum number of matches"),
        current_user: User = Depends(get_current_user)
    ):
        """Get current user's matches"""
        try:
            matches = await matching_service.get_user_matches(current_user.id, status_filter, limit)
            return matches
        except Exception as e:
            logger.error(f"Get matches error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not get matches"
            )
    
    @router.put("/interest/{match_id}")
    async def update_match_interest(
        match_id: str,
        interested: bool = Query(..., description="Whether user is interested in this match"),
        current_user: User = Depends(get_current_user)
    ):
        """Update user interest in a match"""
        try:
            success = await matching_service.update_match_interest(match_id, current_user.id, interested)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Match not found"
                )
            
            action = "accepted" if interested else "declined"
            return {"message": f"Match {action} successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Update match interest error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not update match interest"
            )
    
    @router.get("/suggestions", response_model=List[Dict[str, Any]])
    async def get_match_suggestions(
        limit: int = Query(10, description="Number of suggestions to return"),
        current_user: User = Depends(get_current_user)
    ):
        """Get AI-powered match suggestions"""
        try:
            suggestions = await matching_service.get_match_suggestions(current_user.id, limit)
            return suggestions
        except Exception as e:
            logger.error(f"Get match suggestions error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not get match suggestions"
            )
    
    @router.get("/analytics", response_model=Dict[str, Any])
    async def get_matching_analytics(current_user: User = Depends(get_current_user)):
        """Get matching analytics for current user"""
        try:
            analytics = await matching_service.get_matching_analytics(current_user.id)
            return analytics
        except Exception as e:
            logger.error(f"Get matching analytics error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not get matching analytics"
            )
    
    @router.post("/refresh")
    async def refresh_matches(
        current_user: User = Depends(get_current_user)
    ):
        """Refresh matches for current user"""
        try:
            matches = await matching_service.find_matches(current_user.id, None, 20)
            return {
                "message": "Matches refreshed successfully",
                "new_matches_count": len(matches)
            }
        except Exception as e:
            logger.error(f"Refresh matches error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not refresh matches"
            )
    
    return router