from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List, Optional
import logging
from datetime import datetime

from models import (
    Badge, UserBadge, Achievement, UserAchievement, LeaderboardEntry,
    SkillCoinTransaction, BadgeCreate, AchievementCreate, UserProgress, User
)
from services.gamification_service import GamificationService
from auth import AuthService

logger = logging.getLogger(__name__)
security = HTTPBearer()

def create_gamification_router(db):
    router = APIRouter(prefix="/gamification", tags=["gamification"])
    gamification_service = GamificationService(db)
    auth_service = AuthService(db)
    
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """Get current authenticated user"""
        try:
            token = credentials.credentials
            user = await auth_service.get_current_user(token)
            return user
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )
    
    @router.get("/progress", response_model=UserProgress)
    async def get_user_progress(current_user: User = Depends(get_current_user)):
        """Get comprehensive progress for the current user"""
        try:
            progress = await gamification_service.get_user_progress(current_user.id)
            if not progress:
                raise HTTPException(status_code=404, detail="User progress not found")
            
            return progress
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get user progress")
    
    @router.get("/badges", response_model=List[Badge])
    async def get_all_badges(current_user: User = Depends(get_current_user)):
        """Get all available badges"""
        try:
            badges = await gamification_service.get_all_badges()
            return badges
        except Exception as e:
            logger.error(f"Error getting badges: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get badges")
    
    @router.get("/achievements", response_model=List[Achievement])
    async def get_all_achievements(current_user: User = Depends(get_current_user)):
        """Get all available achievements"""
        try:
            achievements = await gamification_service.get_all_achievements()
            return achievements
        except Exception as e:
            logger.error(f"Error getting achievements: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get achievements")
    
    @router.get("/leaderboard", response_model=List[LeaderboardEntry])
    async def get_leaderboard(
        limit: int = Query(50, ge=1, le=100),
        current_user: User = Depends(get_current_user)
    ):
        """Get the current leaderboard"""
        try:
            leaderboard = await gamification_service.get_leaderboard(limit)
            return leaderboard
        except Exception as e:
            logger.error(f"Error getting leaderboard: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get leaderboard")
    
    @router.get("/transactions", response_model=List[SkillCoinTransaction])
    async def get_user_transactions(
        limit: int = Query(50, ge=1, le=100),
        current_user: User = Depends(get_current_user)
    ):
        """Get user's skill coin transaction history"""
        try:
            transactions = await gamification_service.get_user_transactions(current_user.id, limit)
            return transactions
        except Exception as e:
            logger.error(f"Error getting transactions: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get transactions")
    
    @router.post("/check-progress")
    async def check_user_progress(current_user: User = Depends(get_current_user)):
        """Check user progress and award any earned badges/achievements"""
        try:
            awarded_badges = await gamification_service.check_and_award_badges(current_user.id)
            
            return {
                "message": "Progress checked successfully",
                "new_badges": len(awarded_badges),
                "badges": [{"name": badge.name, "description": badge.description} for badge in awarded_badges]
            }
        except Exception as e:
            logger.error(f"Error checking user progress: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to check progress")
    
    @router.get("/user/{user_id}/progress", response_model=UserProgress)
    async def get_other_user_progress(
        user_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """Get progress for another user (public information only)"""
        try:
            progress = await gamification_service.get_user_progress(user_id)
            if not progress:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Return limited public information
            return UserProgress(
                user_id=progress.user_id,
                skill_coins=progress.skill_coins,
                total_sessions=progress.total_sessions,
                teaching_sessions=progress.teaching_sessions,
                learning_sessions=progress.learning_sessions,
                average_rating=progress.average_rating,
                badges=progress.badges,
                achievements=progress.achievements,
                current_streak=progress.current_streak,
                longest_streak=progress.longest_streak,
                leaderboard_rank=progress.leaderboard_rank,
                recent_activities=[]  # Don't show other users' activities
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get user progress")
    
    @router.post("/award-coins")
    async def award_skill_coins(
        user_id: str,
        amount: int,
        reason: str,
        current_user: User = Depends(get_current_user)
    ):
        """Award skill coins to a user (admin only for now)"""
        try:
            # For now, allow any user to award coins to themselves for testing
            # In production, this should be admin-only
            if user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Can only award coins to yourself for testing")
            
            success = await gamification_service.award_skill_coins(
                user_id=user_id,
                amount=amount,
                transaction_type="bonus",
                source="admin",
                description=reason
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to award coins")
            
            return {"message": f"Successfully awarded {amount} coins", "reason": reason}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error awarding coins: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to award coins")
    
    @router.get("/stats/summary")
    async def get_gamification_stats(current_user: User = Depends(get_current_user)):
        """Get overall gamification statistics"""
        try:
            # Get counts of various gamification elements
            total_badges = await gamification_service.db.badges.count_documents({"is_active": True})
            total_achievements = await gamification_service.db.achievements.count_documents({"is_active": True})
            total_users = await gamification_service.db.users.count_documents({"is_active": True})
            
            # Get leaderboard top user
            leaderboard = await gamification_service.get_leaderboard(1)
            top_user = leaderboard[0] if leaderboard else None
            
            return {
                "total_badges": total_badges,
                "total_achievements": total_achievements,
                "total_users": total_users,
                "top_user": {
                    "username": top_user.username,
                    "skill_coins": top_user.skill_coins,
                    "total_sessions": top_user.total_sessions
                } if top_user else None
            }
            
        except Exception as e:
            logger.error(f"Error getting gamification stats: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get stats")
    
    return router