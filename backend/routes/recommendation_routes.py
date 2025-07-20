from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from auth import AuthService
from models import (
    User, RecommendationCreate, RecommendationResponse,
    RecommendationType, LearningGoal, LearningGoalCreate, LearningGoalUpdate
)
from services.recommendation_service import RecommendationService

security = HTTPBearer()

def create_recommendation_router(db: AsyncIOMotorDatabase) -> APIRouter:
    router = APIRouter()
    auth_service = AuthService(db)
    
    async def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current user from token"""
        return await auth_service.get_current_user(credentials.credentials)

    @router.get("/", response_model=List[RecommendationResponse])
    async def get_recommendations(
        limit: int = Query(10, ge=1, le=50),
        recommendation_types: Optional[str] = Query(None, description="Comma-separated recommendation types"),
        min_confidence: float = Query(0.0, ge=0.0, le=1.0),
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Get personalized recommendations for the user"""
        recommendation_service = RecommendationService(db)
        
        # Parse recommendation types if provided
        types_filter = None
        if recommendation_types:
            try:
                types_filter = [RecommendationType(t.strip()) for t in recommendation_types.split(",")]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid recommendation type")
        
        recommendations = await recommendation_service.get_user_recommendations(
            user_id=current_user.id,
            limit=limit,
            recommendation_types=types_filter,
            min_confidence=min_confidence
        )
        
        return recommendations

    @router.post("/generate")
    async def generate_recommendations(
        recommendation_types: Optional[List[str]] = None,
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Generate fresh AI-powered recommendations for the user"""
        recommendation_service = RecommendationService(db)
        
        # Generate all types of recommendations
        all_recommendations = await recommendation_service.generate_all_recommendations(current_user.id)
        
        # Count recommendations generated
        total_count = sum(len(recs) for recs in all_recommendations.values())
        
        return {
            "success": True,
            "message": f"Generated {total_count} new recommendations",
            "recommendations_by_type": {
                recommendation_type: len(recs) 
                for recommendation_type, recs in all_recommendations.items()
            }
        }

    @router.post("/generate/{recommendation_type}")
    async def generate_specific_recommendations(
        recommendation_type: RecommendationType,
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Generate specific type of recommendations"""
        recommendation_service = RecommendationService(db)
        
        recommendations = []
        
        if recommendation_type == RecommendationType.SKILL_LEARNING:
            recommendations = await recommendation_service.generate_skill_learning_recommendations(current_user.id)
        elif recommendation_type == RecommendationType.USER_MATCH:
            recommendations = await recommendation_service.generate_user_match_recommendations(current_user.id)
        elif recommendation_type == RecommendationType.SESSION_TIMING:
            recommendations = await recommendation_service.generate_session_timing_recommendations(current_user.id)
        elif recommendation_type == RecommendationType.LEARNING_PATH:
            recommendations = await recommendation_service.generate_learning_path_recommendations(current_user.id)
        elif recommendation_type == RecommendationType.COMMUNITY_CONTENT:
            recommendations = await recommendation_service.generate_community_content_recommendations(current_user.id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported recommendation type")
        
        return {
            "success": True,
            "message": f"Generated {len(recommendations)} {recommendation_type} recommendations",
            "count": len(recommendations)
        }

    @router.put("/{recommendation_id}/viewed")
    async def mark_recommendation_viewed(
        recommendation_id: str,
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Mark a recommendation as viewed"""
        recommendation_service = RecommendationService(db)
        success = await recommendation_service.mark_recommendation_viewed(recommendation_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        return {"success": True, "message": "Recommendation marked as viewed"}

    @router.put("/{recommendation_id}/acted-upon")
    async def mark_recommendation_acted_upon(
        recommendation_id: str,
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Mark a recommendation as acted upon"""
        recommendation_service = RecommendationService(db)
        success = await recommendation_service.mark_recommendation_acted_upon(recommendation_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        return {"success": True, "message": "Recommendation marked as acted upon"}

    @router.put("/{recommendation_id}/dismiss")
    async def dismiss_recommendation(
        recommendation_id: str,
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Dismiss a recommendation"""
        recommendation_service = RecommendationService(db)
        success = await recommendation_service.dismiss_recommendation(recommendation_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        return {"success": True, "message": "Recommendation dismissed"}

    # Learning Goals Management
    @router.get("/learning-goals", response_model=List[LearningGoal])
    async def get_learning_goals(
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Get user's learning goals"""
        recommendation_service = RecommendationService(db)
        goals = await recommendation_service.get_user_learning_goals(current_user.id)
        return goals

    @router.post("/learning-goals", response_model=LearningGoal)
    async def create_learning_goal(
        goal_data: LearningGoalCreate,
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Create a new learning goal"""
        recommendation_service = RecommendationService(db)
        
        try:
            goal = await recommendation_service.create_learning_goal(current_user.id, goal_data.dict())
            return goal
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.put("/learning-goals/{goal_id}/progress")
    async def update_goal_progress(
        goal_id: str,
        progress: float = Query(..., ge=0.0, le=100.0, description="Progress percentage (0-100)"),
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Update learning goal progress"""
        recommendation_service = RecommendationService(db)
        success = await recommendation_service.update_goal_progress(goal_id, progress)
        
        if not success:
            raise HTTPException(status_code=404, detail="Learning goal not found")
        
        return {"success": True, "message": "Goal progress updated", "progress": progress}

    # Analytics and Insights
    @router.get("/insights")
    async def get_recommendation_insights(
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Get insights about user's recommendation engagement"""
        recommendation_service = RecommendationService(db)
        
        # Get recommendation statistics
        pipeline = [
            {"$match": {"user_id": current_user.id}},
            {
                "$group": {
                    "_id": "$recommendation_type",
                    "total": {"$sum": 1},
                    "viewed": {"$sum": {"$cond": [{"$eq": ["$is_viewed", True]}, 1, 0]}},
                    "acted_upon": {"$sum": {"$cond": [{"$eq": ["$is_acted_upon", True]}, 1, 0]}},
                    "dismissed": {"$sum": {"$cond": [{"$eq": ["$is_dismissed", True]}, 1, 0]}},
                    "avg_confidence": {"$avg": "$confidence_score"}
                }
            }
        ]
        
        recommendations_collection = recommendation_service.recommendations_collection
        stats = await recommendations_collection.aggregate(pipeline).to_list(length=None)
        
        # Calculate overall engagement metrics
        total_recommendations = sum(stat["total"] for stat in stats)
        total_viewed = sum(stat["viewed"] for stat in stats)
        total_acted_upon = sum(stat["acted_upon"] for stat in stats)
        
        engagement_rate = (total_viewed / total_recommendations * 100) if total_recommendations > 0 else 0
        action_rate = (total_acted_upon / total_viewed * 100) if total_viewed > 0 else 0
        
        return {
            "total_recommendations": total_recommendations,
            "total_viewed": total_viewed,
            "total_acted_upon": total_acted_upon,
            "engagement_rate": round(engagement_rate, 1),
            "action_rate": round(action_rate, 1),
            "by_type": {
                stat["_id"]: {
                    "total": stat["total"],
                    "viewed": stat["viewed"],
                    "acted_upon": stat["acted_upon"],
                    "dismissed": stat["dismissed"],
                    "avg_confidence": round(stat["avg_confidence"], 2),
                    "engagement_rate": round((stat["viewed"] / stat["total"] * 100), 1) if stat["total"] > 0 else 0
                }
                for stat in stats
            }
        }

    @router.get("/dashboard")
    async def get_recommendation_dashboard(
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Get personalized recommendation dashboard with fresh recommendations and insights"""
        recommendation_service = RecommendationService(db)
        
        # Get fresh recommendations (top 3 of each type)
        fresh_recommendations = await recommendation_service.generate_all_recommendations(current_user.id)
        
        # Get top recommendations by confidence
        all_recommendations = await recommendation_service.get_user_recommendations(
            user_id=current_user.id,
            limit=8,
            min_confidence=0.3
        )
        
        # Get learning goals
        learning_goals = await recommendation_service.get_user_learning_goals(current_user.id)
        
        # Calculate quick stats
        total_goals = len(learning_goals)
        active_goals = len([g for g in learning_goals if g.is_active])
        avg_progress = sum(g.current_progress for g in learning_goals) / total_goals if total_goals > 0 else 0
        
        return {
            "recommendations": {
                "featured": all_recommendations[:4],  # Top 4 for featured section
                "by_type": {
                    "skill_learning": [r for r in all_recommendations if r.recommendation_type == RecommendationType.SKILL_LEARNING][:2],
                    "user_matches": [r for r in all_recommendations if r.recommendation_type == RecommendationType.USER_MATCH][:2],
                    "learning_paths": [r for r in all_recommendations if r.recommendation_type == RecommendationType.LEARNING_PATH][:2],
                    "community_content": [r for r in all_recommendations if r.recommendation_type == RecommendationType.COMMUNITY_CONTENT][:2]
                }
            },
            "learning_goals": {
                "total_goals": total_goals,
                "active_goals": active_goals,
                "average_progress": round(avg_progress, 1),
                "recent_goals": learning_goals[:3]  # Show 3 most recent goals
            },
            "quick_stats": {
                "total_recommendations": len(all_recommendations),
                "high_confidence_count": len([r for r in all_recommendations if r.confidence_score >= 0.7]),
                "fresh_generated": sum(len(recs) for recs in fresh_recommendations.values())
            }
        }
    
    return router