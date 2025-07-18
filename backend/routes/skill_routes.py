from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any
from models import Skill, SkillCreate, User
from services.skill_service import SkillService
from auth import AuthService
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

def create_skill_router(db: AsyncIOMotorClient) -> APIRouter:
    router = APIRouter(prefix="/skills", tags=["Skills"])
    skill_service = SkillService(db)
    auth_service = AuthService(db)
    
    async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
        """Get current authenticated user (optional)"""
        if not credentials:
            return None
        try:
            token = credentials.credentials
            return await auth_service.get_current_user(token)
        except:
            return None
    
    @router.post("/", response_model=Skill)
    async def create_skill(
        skill_data: SkillCreate,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Create a new skill"""
        # Verify user is authenticated
        try:
            token = credentials.credentials
            await auth_service.get_current_user(token)
        except:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        try:
            return await skill_service.create_skill(skill_data)
        except Exception as e:
            logger.error(f"Create skill error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.get("/{skill_id}", response_model=Skill)
    async def get_skill(skill_id: str):
        """Get skill by ID"""
        skill = await skill_service.get_skill(skill_id)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found"
            )
        return skill
    
    @router.get("/", response_model=List[Skill])
    async def get_all_skills(
        category: Optional[str] = Query(None, description="Filter by category"),
        limit: int = Query(100, description="Maximum number of results")
    ):
        """Get all skills"""
        return await skill_service.get_all_skills(category, limit)
    
    @router.get("/search/query", response_model=List[Skill])
    async def search_skills(
        query: str = Query(..., description="Search query"),
        category: Optional[str] = Query(None, description="Filter by category"),
        limit: int = Query(20, description="Maximum number of results")
    ):
        """Search skills"""
        return await skill_service.search_skills(query, category, limit)
    
    @router.get("/popular/list", response_model=List[Skill])
    async def get_popular_skills(
        limit: int = Query(10, description="Number of popular skills to return")
    ):
        """Get most popular skills"""
        return await skill_service.get_popular_skills(limit)
    
    @router.get("/categories/list", response_model=List[Dict[str, Any]])
    async def get_skill_categories():
        """Get all skill categories with counts"""
        return await skill_service.get_skill_categories()
    
    @router.get("/trending/list", response_model=List[Dict[str, Any]])
    async def get_trending_skills(
        days: int = Query(7, description="Number of days to look back"),
        limit: int = Query(10, description="Number of trending skills to return")
    ):
        """Get trending skills"""
        return await skill_service.get_trending_skills(days, limit)
    
    @router.get("/suggestions/list", response_model=List[Skill])
    async def get_skill_suggestions(
        user_skills: List[str] = Query([], description="User's current skills"),
        limit: int = Query(5, description="Number of suggestions to return")
    ):
        """Get skill suggestions based on user's current skills"""
        return await skill_service.suggest_skills(user_skills, limit)
    
    @router.get("/statistics/{skill_id}", response_model=Dict[str, Any])
    async def get_skill_statistics(skill_id: str):
        """Get detailed statistics for a skill"""
        stats = await skill_service.get_skill_statistics(skill_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found"
            )
        return stats
    
    @router.put("/popularity/{skill_id}")
    async def update_skill_popularity(
        skill_id: str,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Update skill popularity score"""
        # Verify user is authenticated
        try:
            token = credentials.credentials
            await auth_service.get_current_user(token)
        except:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        success = await skill_service.update_skill_popularity(skill_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found"
            )
        return {"message": "Skill popularity updated successfully"}
    
    @router.post("/initialize-defaults")
    async def initialize_default_skills(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Initialize default skills (admin only)"""
        # Verify user is authenticated
        try:
            token = credentials.credentials
            user = await auth_service.get_current_user(token)
        except:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        try:
            await skill_service.create_default_skills()
            return {"message": "Default skills initialized successfully"}
        except Exception as e:
            logger.error(f"Initialize default skills error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not initialize default skills"
            )
    
    return router