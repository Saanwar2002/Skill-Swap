from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any
from models import UserResponse, UserUpdate, UserSkill, UserSkillCreate, User
from services.user_service import UserService
from auth import AuthService
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

def create_user_router(db: AsyncIOMotorClient) -> APIRouter:
    router = APIRouter(prefix="/users", tags=["Users"])
    user_service = UserService(db)
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
    
    @router.get("/profile", response_model=UserResponse)
    async def get_my_profile(current_user: User = Depends(get_current_user)):
        """Get current user's profile"""
        return UserResponse(**current_user.dict(), average_rating=current_user.average_rating)
    
    @router.get("/profile/{user_id}", response_model=UserResponse)
    async def get_user_profile(user_id: str):
        """Get user profile by ID"""
        profile = await user_service.get_user_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return profile
    
    @router.put("/profile", response_model=UserResponse)
    async def update_profile(
        update_data: UserUpdate,
        current_user: User = Depends(get_current_user)
    ):
        """Update current user's profile"""
        try:
            profile = await user_service.update_user_profile(current_user.id, update_data)
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return profile
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.post("/skills", response_model=UserSkill)
    async def add_skill(
        skill_data: UserSkillCreate,
        current_user: User = Depends(get_current_user)
    ):
        """Add skill to current user's profile"""
        try:
            return await user_service.add_user_skill(current_user.id, skill_data)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Add skill error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not add skill"
            )
    
    @router.get("/skills", response_model=List[UserSkill])
    async def get_my_skills(current_user: User = Depends(get_current_user)):
        """Get current user's skills"""
        return await user_service.get_user_skills(current_user.id)
    
    @router.get("/skills/{user_id}", response_model=List[UserSkill])
    async def get_user_skills(user_id: str):
        """Get skills for a specific user"""
        return await user_service.get_user_skills(user_id)
    
    @router.put("/skills/{skill_id}", response_model=UserSkill)
    async def update_skill(
        skill_id: str,
        update_data: Dict[str, Any],
        current_user: User = Depends(get_current_user)
    ):
        """Update user skill"""
        skill = await user_service.update_user_skill(current_user.id, skill_id, update_data)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found"
            )
        return skill
    
    @router.delete("/skills/{skill_id}")
    async def remove_skill(
        skill_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Remove skill from current user's profile"""
        success = await user_service.remove_user_skill(current_user.id, skill_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found"
            )
        return {"message": "Skill removed successfully"}
    
    @router.post("/skills/{user_id}/{skill_id}/endorse")
    async def endorse_skill(
        user_id: str,
        skill_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Endorse a user's skill"""
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot endorse your own skill"
            )
        
        success = await user_service.endorse_skill(current_user.id, user_id, skill_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not endorse skill"
            )
        return {"message": "Skill endorsed successfully"}
    
    @router.delete("/skills/{user_id}/{skill_id}/endorse")
    async def remove_endorsement(
        user_id: str,
        skill_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Remove endorsement from a user's skill"""
        success = await user_service.remove_endorsement(current_user.id, user_id, skill_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not remove endorsement"
            )
        return {"message": "Endorsement removed successfully"}
    
    @router.get("/search", response_model=List[UserResponse])
    async def search_users(
        query: Optional[str] = Query(None, description="Search query"),
        skills_offered: Optional[List[str]] = Query(None, description="Skills offered filter"),
        skills_wanted: Optional[List[str]] = Query(None, description="Skills wanted filter"),
        location: Optional[str] = Query(None, description="Location filter"),
        min_rating: Optional[float] = Query(None, description="Minimum rating filter"),
        limit: int = Query(20, description="Maximum number of results")
    ):
        """Search users"""
        filters = {}
        if skills_offered:
            filters["skills_offered"] = skills_offered
        if skills_wanted:
            filters["skills_wanted"] = skills_wanted
        if location:
            filters["location"] = location
        if min_rating:
            filters["min_rating"] = min_rating
        
        return await user_service.search_users(query or "", filters, limit)
    
    @router.get("/by-skills", response_model=List[UserResponse])
    async def get_users_by_skills(
        skills: List[str] = Query(..., description="Skills to search for"),
        limit: int = Query(20, description="Maximum number of results"),
        current_user: User = Depends(get_current_user)
    ):
        """Get users who offer specific skills"""
        return await user_service.get_user_by_skills(skills, current_user.id, limit)
    
    @router.get("/wanting-skills", response_model=List[UserResponse])
    async def get_users_wanting_skills(
        skills: List[str] = Query(..., description="Skills to search for"),
        limit: int = Query(20, description="Maximum number of results"),
        current_user: User = Depends(get_current_user)
    ):
        """Get users who want to learn specific skills"""
        return await user_service.get_users_wanting_skills(skills, current_user.id, limit)
    
    @router.put("/preferences")
    async def update_skill_preferences(
        skills_offered: Optional[List[str]] = None,
        skills_wanted: Optional[List[str]] = None,
        current_user: User = Depends(get_current_user)
    ):
        """Update user skill preferences"""
        success = await user_service.update_user_preferences(
            current_user.id, skills_offered, skills_wanted
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update preferences"
            )
        return {"message": "Preferences updated successfully"}
    
    @router.get("/statistics", response_model=Dict[str, Any])
    async def get_my_statistics(current_user: User = Depends(get_current_user)):
        """Get current user's statistics"""
        return await user_service.get_user_statistics(current_user.id)
    
    @router.get("/statistics/{user_id}", response_model=Dict[str, Any])
    async def get_user_statistics(user_id: str):
        """Get user statistics"""
        stats = await user_service.get_user_statistics(user_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return stats
    
    @router.get("/leaderboard", response_model=List[Dict[str, Any]])
    async def get_leaderboard(
        category: str = Query("experience", description="Leaderboard category"),
        limit: int = Query(10, description="Number of users to return")
    ):
        """Get leaderboard"""
        valid_categories = ["experience", "sessions", "rating", "coins"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )
        
        return await user_service.get_leaderboard(category, limit)
    
    return router