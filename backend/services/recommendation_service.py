from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from models import (
    Recommendation, RecommendationCreate, RecommendationResponse,
    RecommendationType, LearningGoal, UserAnalytics, SkillLevel
)
from services.matching_service import MatchingService
import random
import uuid


class RecommendationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.recommendations_collection = db["recommendations"]
        self.learning_goals_collection = db["learning_goals"]
        self.analytics_collection = db["user_analytics"]
        self.users_collection = db["users"]
        self.skills_collection = db["skills"]
        self.sessions_collection = db["sessions"]
        self.matching_service = MatchingService(db)
    
    async def create_recommendation(self, recommendation_data: RecommendationCreate) -> Recommendation:
        """Create a new recommendation"""
        recommendation = Recommendation(**recommendation_data.dict())
        await self.recommendations_collection.insert_one(recommendation.dict())
        return recommendation
    
    async def get_user_recommendations(
        self, 
        user_id: str, 
        limit: int = 10,
        recommendation_types: Optional[List[RecommendationType]] = None,
        min_confidence: float = 0.0
    ) -> List[RecommendationResponse]:
        """Get recommendations for a user"""
        query = {
            "user_id": user_id,
            "is_dismissed": False,
            "confidence_score": {"$gte": min_confidence}
        }
        
        # Add expiration filter
        query["$or"] = [
            {"expires_at": None},
            {"expires_at": {"$gt": datetime.utcnow()}}
        ]
        
        if recommendation_types:
            query["recommendation_type"] = {"$in": recommendation_types}
        
        cursor = self.recommendations_collection.find(query).sort("confidence_score", -1).limit(limit)
        recommendations = await cursor.to_list(length=limit)
        
        # Convert to response models
        response_recommendations = []
        for rec in recommendations:
            response_rec = RecommendationResponse(
                **rec,
                time_ago=self._get_time_ago(rec["created_at"])
            )
            response_recommendations.append(response_rec)
        
        return response_recommendations
    
    async def mark_recommendation_viewed(self, recommendation_id: str, user_id: str) -> bool:
        """Mark recommendation as viewed"""
        result = await self.recommendations_collection.update_one(
            {"id": recommendation_id, "user_id": user_id},
            {
                "$set": {
                    "is_viewed": True,
                    "viewed_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    async def mark_recommendation_acted_upon(self, recommendation_id: str, user_id: str) -> bool:
        """Mark recommendation as acted upon"""
        result = await self.recommendations_collection.update_one(
            {"id": recommendation_id, "user_id": user_id},
            {
                "$set": {
                    "is_acted_upon": True,
                    "acted_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    async def dismiss_recommendation(self, recommendation_id: str, user_id: str) -> bool:
        """Dismiss a recommendation"""
        result = await self.recommendations_collection.update_one(
            {"id": recommendation_id, "user_id": user_id},
            {"$set": {"is_dismissed": True}}
        )
        return result.modified_count > 0
    
    # AI-Powered Recommendation Generators
    async def generate_skill_learning_recommendations(self, user_id: str) -> List[Recommendation]:
        """Generate skill learning recommendations based on user profile and activity"""
        user = await self.users_collection.find_one({"id": user_id})
        if not user:
            return []
        
        recommendations = []
        
        # Get user's current skills
        current_skills = set(skill.lower() for skill in user.get("skills_offered", []))
        
        # Get skill IDs from skill names (we need to look them up)
        current_skill_ids = set()
        if current_skills:
            # Look up skill IDs from skill names
            skills_cursor = self.skills_collection.find({"name": {"$in": list(current_skills)}})
            skills_docs = await skills_cursor.to_list(length=None)
            current_skill_ids = set(skill["id"] for skill in skills_docs)
        
        # Get popular complementary skills
        complementary_skills = await self._get_complementary_skills(current_skill_ids)
        
        for skill in complementary_skills[:3]:  # Top 3 recommendations
            # Calculate confidence based on skill popularity and user activity
            confidence = min(0.9, 0.5 + (skill.get("popularity_score", 0) * 0.4))
            
            recommendation_data = RecommendationCreate(
                user_id=user_id,
                recommendation_type=RecommendationType.SKILL_LEARNING,
                title=f"Learn {skill['name']}",
                description=f"Based on your {', '.join(list(current_skills)[:2])} skills, learning {skill['name']} could open up new opportunities. {skill.get('learners_count', 0)} users are currently learning this skill.",
                confidence_score=confidence,
                data={
                    "skill_id": skill["id"],
                    "skill_name": skill["name"],
                    "category": skill.get("category", ""),
                    "complementary_skills": list(current_skills)[:3],
                    "estimated_sessions": skill.get("avg_sessions_to_learn", 5),
                    "available_teachers": skill.get("teachers_count", 0)
                },
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            
            recommendation = await self.create_recommendation(recommendation_data)
            recommendations.append(recommendation)
        
        return recommendations
    
    async def generate_user_match_recommendations(self, user_id: str) -> List[Recommendation]:
        """Generate user match recommendations using AI matching"""
        recommendations = []
        
        # Get fresh matches using the existing matching service
        matches = await self.matching_service.find_matches_for_user(user_id, limit=5)
        
        for match in matches[:3]:  # Top 3 match recommendations
            match_user = await self.users_collection.find_one({"id": match["user_id"]})
            if not match_user:
                continue
            
            recommendation_data = RecommendationCreate(
                user_id=user_id,
                recommendation_type=RecommendationType.USER_MATCH,
                title=f"Connect with {match_user['first_name']} {match_user['last_name']}",
                description=f"You have a {match['compatibility_score']:.0%} compatibility match! They can help you with {', '.join(match['matching_skills'][:2])} and you can share your expertise in return.",
                confidence_score=match["compatibility_score"],
                data={
                    "match_user_id": match["user_id"],
                    "compatibility_score": match["compatibility_score"],
                    "matching_skills": match["matching_skills"],
                    "common_interests": match.get("common_interests", []),
                    "user_avatar": match_user.get("profile_image"),
                    "user_rating": match_user.get("average_rating", 0),
                    "user_location": match_user.get("location")
                },
                expires_at=datetime.utcnow() + timedelta(days=3)
            )
            
            recommendation = await self.create_recommendation(recommendation_data)
            recommendations.append(recommendation)
        
        return recommendations
    
    async def generate_session_timing_recommendations(self, user_id: str) -> List[Recommendation]:
        """Generate optimal session timing recommendations"""
        recommendations = []
        
        # Analyze user's session patterns
        session_pattern = await self._analyze_user_session_patterns(user_id)
        
        if session_pattern["peak_hours"]:
            peak_hours = session_pattern["peak_hours"]
            success_rate = session_pattern["success_rate"]
            
            recommendation_data = RecommendationCreate(
                user_id=user_id,
                recommendation_type=RecommendationType.SESSION_TIMING,
                title="Optimize Your Learning Schedule",
                description=f"Based on your activity patterns, you're most successful learning between {peak_hours[0]}:00-{peak_hours[1]}:00. Sessions during these hours have a {success_rate:.0%} completion rate for you.",
                confidence_score=min(0.9, 0.6 + (success_rate * 0.3)),
                data={
                    "optimal_hours": peak_hours,
                    "success_rate": success_rate,
                    "total_sessions_analyzed": session_pattern["total_sessions"],
                    "suggested_frequency": session_pattern["suggested_frequency"]
                },
                expires_at=datetime.utcnow() + timedelta(days=14)
            )
            
            recommendation = await self.create_recommendation(recommendation_data)
            recommendations.append(recommendation)
        
        return recommendations
    
    async def generate_learning_path_recommendations(self, user_id: str) -> List[Recommendation]:
        """Generate structured learning path recommendations"""
        user = await self.users_collection.find_one({"id": user_id})
        if not user:
            return []
        
        recommendations = []
        
        # Get user's learning goals or interests
        learning_goals = await self.learning_goals_collection.find({"user_id": user_id, "is_active": True}).to_list(length=10)
        
        # If no explicit goals, infer from profile and activity
        if not learning_goals:
            learning_goals = await self._infer_learning_goals(user_id)
        
        for goal in learning_goals[:2]:  # Top 2 learning path recommendations
            # Create a structured learning path
            path = await self._create_learning_path(goal["skill_id"] if "skill_id" in goal else goal.get("target_skill_id"))
            
            if path:
                recommendation_data = RecommendationCreate(
                    user_id=user_id,
                    recommendation_type=RecommendationType.LEARNING_PATH,
                    title=f"Structured Path: {path['skill_name']}",
                    description=f"Follow this {path['duration_weeks']}-week path to master {path['skill_name']}. Includes {len(path['milestones'])} key milestones and connects you with the right teachers at each stage.",
                    confidence_score=0.8,
                    data={
                        "skill_id": path["skill_id"],
                        "skill_name": path["skill_name"],
                        "duration_weeks": path["duration_weeks"],
                        "milestones": path["milestones"],
                        "estimated_sessions": path["total_sessions"],
                        "estimated_cost": path["total_coins"]
                    },
                    expires_at=datetime.utcnow() + timedelta(days=30)
                )
                
                recommendation = await self.create_recommendation(recommendation_data)
                recommendations.append(recommendation)
        
        return recommendations
    
    async def generate_community_content_recommendations(self, user_id: str) -> List[Recommendation]:
        """Generate community content recommendations"""
        user = await self.users_collection.find_one({"id": user_id})
        if not user:
            return []
        
        recommendations = []
        
        # Get user's skill interests
        user_skills = [skill.lower() for skill in user.get("skills_offered", [])]
        user_interests = [skill.lower() for skill in user.get("skills_wanted", [])]
        all_interests = set(user_skills + user_interests)
        
        # Find relevant community posts
        community_posts = await self._find_relevant_community_content(all_interests)
        
        for post in community_posts[:2]:  # Top 2 content recommendations
            recommendation_data = RecommendationCreate(
                user_id=user_id,
                recommendation_type=RecommendationType.COMMUNITY_CONTENT,
                title=f"Trending: {post['title'][:50]}{'...' if len(post['title']) > 50 else ''}",
                description=f"This popular {post['post_type']} in the {post['forum_name']} forum has {post['likes_count']} likes and matches your interests in {', '.join(post['relevant_skills'][:2])}.",
                confidence_score=min(0.9, 0.4 + (post["engagement_score"] * 0.5)),
                data={
                    "post_id": post["id"],
                    "post_title": post["title"],
                    "post_type": post["post_type"],
                    "forum_name": post["forum_name"],
                    "author_name": post["author_name"],
                    "likes_count": post["likes_count"],
                    "comments_count": post["comments_count"],
                    "relevant_skills": post["relevant_skills"]
                },
                expires_at=datetime.utcnow() + timedelta(days=5)
            )
            
            recommendation = await self.create_recommendation(recommendation_data)
            recommendations.append(recommendation)
        
        return recommendations
    
    async def generate_all_recommendations(self, user_id: str) -> Dict[str, List[Recommendation]]:
        """Generate all types of recommendations for a user"""
        # Clean up old recommendations first
        await self._cleanup_old_recommendations(user_id)
        
        recommendations = {}
        
        # Generate different types of recommendations
        recommendations["skill_learning"] = await self.generate_skill_learning_recommendations(user_id)
        recommendations["user_matches"] = await self.generate_user_match_recommendations(user_id)
        recommendations["session_timing"] = await self.generate_session_timing_recommendations(user_id)
        recommendations["learning_paths"] = await self.generate_learning_path_recommendations(user_id)
        recommendations["community_content"] = await self.generate_community_content_recommendations(user_id)
        
        return recommendations
    
    # Learning Goals Management
    async def create_learning_goal(self, user_id: str, goal_data: Dict[str, Any]) -> LearningGoal:
        """Create a learning goal for user"""
        # Get skill information
        skill = await self.skills_collection.find_one({"id": goal_data["skill_id"]})
        if not skill:
            raise ValueError("Skill not found")
        
        goal = LearningGoal(
            user_id=user_id,
            skill_id=goal_data["skill_id"],
            skill_name=skill["name"],
            target_level=goal_data.get("target_level", SkillLevel.INTERMEDIATE),
            target_date=goal_data.get("target_date"),
            weekly_session_target=goal_data.get("weekly_session_target", 2)
        )
        
        await self.learning_goals_collection.insert_one(goal.dict())
        return goal
    
    async def get_user_learning_goals(self, user_id: str) -> List[LearningGoal]:
        """Get user's learning goals"""
        goals = await self.learning_goals_collection.find({"user_id": user_id, "is_active": True}).to_list(length=None)
        return [LearningGoal(**goal) for goal in goals]
    
    async def update_goal_progress(self, goal_id: str, progress: float) -> bool:
        """Update learning goal progress"""
        update_data = {
            "current_progress": min(100.0, max(0.0, progress)),
            "updated_at": datetime.utcnow()
        }
        
        # Mark as completed if 100% progress
        if progress >= 100.0:
            update_data["completed_at"] = datetime.utcnow()
            update_data["is_active"] = False
        
        result = await self.learning_goals_collection.update_one(
            {"id": goal_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # Private helper methods
    async def _get_complementary_skills(self, current_skill_ids: set) -> List[Dict[str, Any]]:
        """Get skills that complement the user's current skills"""
        # Get all skills with statistics
        pipeline = [
            {
                "$match": {
                    "id": {"$nin": list(current_skill_ids)},
                    "is_active": True
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "let": {"skill_id": "$id"},
                    "pipeline": [
                        {"$unwind": "$skills_offered"},
                        {"$match": {"$expr": {"$eq": ["$skills_offered.skill_id", "$$skill_id"]}}},
                        {"$count": "count"}
                    ],
                    "as": "teachers"
                }
            },
            {
                "$lookup": {
                    "from": "users", 
                    "let": {"skill_id": "$id"},
                    "pipeline": [
                        {"$unwind": "$skills_wanted"},
                        {"$match": {"$expr": {"$eq": ["$skills_wanted.skill_id", "$$skill_id"]}}},
                        {"$count": "count"}
                    ],
                    "as": "learners"
                }
            },
            {
                "$addFields": {
                    "teachers_count": {"$ifNull": [{"$arrayElemAt": ["$teachers.count", 0]}, 0]},
                    "learners_count": {"$ifNull": [{"$arrayElemAt": ["$learners.count", 0]}, 0]},
                    "popularity_score": {
                        "$divide": [
                            {"$add": [
                                {"$ifNull": [{"$arrayElemAt": ["$teachers.count", 0]}, 0]},
                                {"$ifNull": [{"$arrayElemAt": ["$learners.count", 0]}, 0]}
                            ]},
                            2
                        ]
                    }
                }
            },
            {"$sort": {"popularity_score": -1}},
            {"$limit": 10}
        ]
        
        skills = await self.skills_collection.aggregate(pipeline).to_list(length=10)
        return skills
    
    async def _analyze_user_session_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's session patterns to recommend optimal timing"""
        # Get user's completed sessions
        sessions = await self.sessions_collection.find({
            "$or": [{"teacher_id": user_id}, {"learner_id": user_id}],
            "status": "completed"
        }).to_list(length=None)
        
        if not sessions:
            return {"peak_hours": [], "success_rate": 0, "total_sessions": 0, "suggested_frequency": 1}
        
        # Analyze session timing patterns
        hour_success = {}
        total_sessions = len(sessions)
        
        for session in sessions:
            hour = session["starts_at"].hour
            if hour not in hour_success:
                hour_success[hour] = {"total": 0, "completed": 0}
            
            hour_success[hour]["total"] += 1
            if session["status"] == "completed":
                hour_success[hour]["completed"] += 1
        
        # Find peak performance hours
        best_hours = []
        best_success_rate = 0
        
        for hour, stats in hour_success.items():
            success_rate = stats["completed"] / stats["total"] if stats["total"] > 0 else 0
            if success_rate > best_success_rate and stats["total"] >= 2:  # At least 2 sessions
                best_success_rate = success_rate
                best_hours = [hour, hour + 1]
        
        # Calculate suggested frequency based on current patterns
        avg_sessions_per_week = total_sessions / max(1, (datetime.utcnow() - sessions[-1]["created_at"]).days / 7)
        suggested_frequency = max(1, int(avg_sessions_per_week * 1.2))  # 20% increase
        
        return {
            "peak_hours": best_hours,
            "success_rate": best_success_rate,
            "total_sessions": total_sessions,
            "suggested_frequency": min(suggested_frequency, 5)  # Cap at 5 sessions per week
        }
    
    async def _infer_learning_goals(self, user_id: str) -> List[Dict[str, Any]]:
        """Infer learning goals from user profile and activity"""
        user = await self.users_collection.find_one({"id": user_id})
        if not user:
            return []
        
        goals = []
        
        # Goals from skills_wanted
        for skill in user.get("skills_wanted", [])[:3]:
            goals.append({
                "skill_id": skill["skill_id"],
                "target_skill_id": skill["skill_id"],
                "confidence": 0.8
            })
        
        return goals
    
    async def _create_learning_path(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Create a structured learning path for a skill"""
        skill = await self.skills_collection.find_one({"id": skill_id})
        if not skill:
            return None
        
        # Create a basic learning path structure
        # In a real implementation, this could be much more sophisticated
        
        levels = [
            {"level": "Beginner", "sessions": 3, "weeks": 2, "coins": 150},
            {"level": "Intermediate", "sessions": 5, "weeks": 4, "coins": 300},
            {"level": "Advanced", "sessions": 4, "weeks": 3, "coins": 250}
        ]
        
        milestones = []
        total_sessions = 0
        total_weeks = 0
        total_coins = 0
        
        for i, level in enumerate(levels):
            milestones.append({
                "milestone": i + 1,
                "title": f"{level['level']} {skill['name']}",
                "description": f"Complete {level['sessions']} sessions to reach {level['level']} level",
                "sessions_required": level["sessions"],
                "estimated_weeks": level["weeks"],
                "skills_covered": [f"{skill['name']} - {level['level']}"],
                "coin_cost": level["coins"]
            })
            
            total_sessions += level["sessions"]
            total_weeks += level["weeks"]
            total_coins += level["coins"]
        
        return {
            "skill_id": skill_id,
            "skill_name": skill["name"],
            "duration_weeks": total_weeks,
            "total_sessions": total_sessions,
            "total_coins": total_coins,
            "milestones": milestones
        }
    
    async def _find_relevant_community_content(self, user_interests: set) -> List[Dict[str, Any]]:
        """Find relevant community content based on user interests"""
        # Get recent popular posts that match user interests
        pipeline = [
            {
                "$match": {
                    "status": "published",
                    "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)},
                    "$or": [
                        {"tags": {"$in": list(user_interests)}},
                        {"title": {"$regex": "|".join(user_interests), "$options": "i"}}
                    ]
                }
            },
            {
                "$addFields": {
                    "engagement_score": {
                        "$add": [
                            {"$multiply": ["$likes_count", 2]},
                            "$comments_count",
                            {"$divide": ["$views", 10]}
                        ]
                    },
                    "relevant_skills": {
                        "$filter": {
                            "input": "$tags",
                            "as": "tag",
                            "cond": {"$in": ["$$tag", list(user_interests)]}
                        }
                    }
                }
            },
            {"$sort": {"engagement_score": -1}},
            {"$limit": 5}
        ]
        
        posts_collection = self.db["community_posts"]
        posts = await posts_collection.aggregate(pipeline).to_list(length=5)
        
        return posts
    
    async def _cleanup_old_recommendations(self, user_id: str):
        """Clean up old and expired recommendations"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        await self.recommendations_collection.delete_many({
            "user_id": user_id,
            "$or": [
                {"expires_at": {"$lt": datetime.utcnow()}},
                {"created_at": {"$lt": cutoff_date}, "is_viewed": True}
            ]
        })
    
    def _get_time_ago(self, timestamp: datetime) -> str:
        """Get human readable time ago string"""
        now = datetime.utcnow()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} days ago" if diff.days > 1 else "1 day ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago" if hours > 1 else "1 hour ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago" if minutes > 1 else "1 minute ago"
        else:
            return "Just now"