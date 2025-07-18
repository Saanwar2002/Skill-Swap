from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from models import User, UserResponse, UserUpdate, UserSkill, UserSkillCreate, SkillLevel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse with calculated fields"""
    user_dict = user.dict()
    user_dict["average_rating"] = user.average_rating
    return UserResponse(**user_dict)

class UserService:
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.users_collection = db.users
        self.user_skills_collection = db.user_skills
        
    async def get_user_profile(self, user_id: str) -> Optional[UserResponse]:
        """Get user profile with public information"""
        user_data = await self.users_collection.find_one({"id": user_id})
        if not user_data:
            return None
        
        user = User(**user_data)
        return user_to_response(user)
    
    async def update_user_profile(self, user_id: str, update_data: UserUpdate) -> Optional[UserResponse]:
        """Update user profile"""
        update_dict = update_data.dict(exclude_unset=True)
        if not update_dict:
            return await self.get_user_profile(user_id)
        
        update_dict["updated_at"] = datetime.utcnow()
        
        result = await self.users_collection.update_one(
            {"id": user_id},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            return None
        
        return await self.get_user_profile(user_id)
    
    async def add_user_skill(self, user_id: str, skill_data: UserSkillCreate) -> UserSkill:
        """Add skill to user profile"""
        # Check if skill already exists for user
        existing_skill = await self.user_skills_collection.find_one({
            "user_id": user_id,
            "skill_id": skill_data.skill_id
        })
        
        if existing_skill:
            raise ValueError("Skill already exists for this user")
        
        skill_dict = skill_data.dict()
        skill_dict["id"] = f"{user_id}_{skill_data.skill_id}"
        skill_dict["user_id"] = user_id
        skill_dict["endorsements"] = []
        skill_dict["verified"] = False
        skill_dict["created_at"] = datetime.utcnow()
        skill_dict["updated_at"] = datetime.utcnow()
        
        user_skill = UserSkill(**skill_dict)
        await self.user_skills_collection.insert_one(user_skill.dict())
        
        # Add skill to user's skills_offered list
        await self.users_collection.update_one(
            {"id": user_id},
            {"$addToSet": {"skills_offered": skill_data.skill_name}}
        )
        
        return user_skill
    
    async def get_user_skills(self, user_id: str) -> List[UserSkill]:
        """Get all skills for a user"""
        skills_data = await self.user_skills_collection.find({"user_id": user_id}).to_list(None)
        return [UserSkill(**skill) for skill in skills_data]
    
    async def update_user_skill(self, user_id: str, skill_id: str, update_data: Dict[str, Any]) -> Optional[UserSkill]:
        """Update user skill"""
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.user_skills_collection.update_one(
            {"user_id": user_id, "skill_id": skill_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return None
        
        skill_data = await self.user_skills_collection.find_one({"user_id": user_id, "skill_id": skill_id})
        return UserSkill(**skill_data)
    
    async def remove_user_skill(self, user_id: str, skill_id: str) -> bool:
        """Remove skill from user profile"""
        # Get skill name before deletion
        skill_data = await self.user_skills_collection.find_one({"user_id": user_id, "skill_id": skill_id})
        if not skill_data:
            return False
        
        skill_name = skill_data["skill_name"]
        
        # Remove skill from user_skills collection
        result = await self.user_skills_collection.delete_one({"user_id": user_id, "skill_id": skill_id})
        
        if result.deleted_count > 0:
            # Remove skill from user's skills_offered list
            await self.users_collection.update_one(
                {"id": user_id},
                {"$pull": {"skills_offered": skill_name}}
            )
            return True
        
        return False
    
    async def endorse_skill(self, endorser_id: str, user_id: str, skill_id: str) -> bool:
        """Endorse a user's skill"""
        # Check if already endorsed
        existing_endorsement = await self.user_skills_collection.find_one({
            "user_id": user_id,
            "skill_id": skill_id,
            "endorsements": endorser_id
        })
        
        if existing_endorsement:
            return False
        
        # Add endorsement
        result = await self.user_skills_collection.update_one(
            {"user_id": user_id, "skill_id": skill_id},
            {"$addToSet": {"endorsements": endorser_id}}
        )
        
        return result.matched_count > 0
    
    async def remove_endorsement(self, endorser_id: str, user_id: str, skill_id: str) -> bool:
        """Remove endorsement from a user's skill"""
        result = await self.user_skills_collection.update_one(
            {"user_id": user_id, "skill_id": skill_id},
            {"$pull": {"endorsements": endorser_id}}
        )
        
        return result.matched_count > 0
    
    async def search_users(self, query: str, filters: Dict[str, Any] = None, limit: int = 20) -> List[UserResponse]:
        """Search users by username, skills, or location"""
        search_filter = {"is_active": True}
        
        if query:
            search_filter["$or"] = [
                {"username": {"$regex": query, "$options": "i"}},
                {"first_name": {"$regex": query, "$options": "i"}},
                {"last_name": {"$regex": query, "$options": "i"}},
                {"skills_offered": {"$regex": query, "$options": "i"}},
                {"skills_wanted": {"$regex": query, "$options": "i"}},
                {"location": {"$regex": query, "$options": "i"}},
                {"bio": {"$regex": query, "$options": "i"}}
            ]
        
        if filters:
            if "skills_offered" in filters:
                search_filter["skills_offered"] = {"$in": filters["skills_offered"]}
            if "skills_wanted" in filters:
                search_filter["skills_wanted"] = {"$in": filters["skills_wanted"]}
            if "location" in filters:
                search_filter["location"] = {"$regex": filters["location"], "$options": "i"}
            if "min_rating" in filters:
                search_filter["$expr"] = {
                    "$gte": [
                        {"$cond": [{"$eq": ["$rating_count", 0]}, 0, {"$divide": ["$total_rating", "$rating_count"]}]},
                        filters["min_rating"]
                    ]
                }
        
        users_data = await self.users_collection.find(search_filter).limit(limit).to_list(None)
        return [user_to_response(User(**user)) for user in users_data]
    
    async def get_user_by_skills(self, skills: List[str], exclude_user_id: str = None, limit: int = 20) -> List[UserResponse]:
        """Get users who offer specific skills"""
        search_filter = {
            "is_active": True,
            "skills_offered": {"$in": skills}
        }
        
        if exclude_user_id:
            search_filter["id"] = {"$ne": exclude_user_id}
        
        users_data = await self.users_collection.find(search_filter).limit(limit).to_list(None)
        return [user_to_response(User(**user)) for user in users_data]
    
    async def get_users_wanting_skills(self, skills: List[str], exclude_user_id: str = None, limit: int = 20) -> List[UserResponse]:
        """Get users who want to learn specific skills"""
        search_filter = {
            "is_active": True,
            "skills_wanted": {"$in": skills}
        }
        
        if exclude_user_id:
            search_filter["id"] = {"$ne": exclude_user_id}
        
        users_data = await self.users_collection.find(search_filter).limit(limit).to_list(None)
        return [user_to_response(User(**user)) for user in users_data]
    
    async def update_user_preferences(self, user_id: str, skills_offered: List[str] = None, skills_wanted: List[str] = None) -> bool:
        """Update user skill preferences"""
        update_data = {"updated_at": datetime.utcnow()}
        
        if skills_offered is not None:
            update_data["skills_offered"] = skills_offered
        if skills_wanted is not None:
            update_data["skills_wanted"] = skills_wanted
        
        result = await self.users_collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        return result.matched_count > 0
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get detailed user statistics"""
        user_data = await self.users_collection.find_one({"id": user_id})
        if not user_data:
            return {}
        
        user = User(**user_data)
        skills_data = await self.user_skills_collection.find({"user_id": user_id}).to_list(None)
        
        # Calculate additional statistics
        total_endorsements = sum(len(skill.get("endorsements", [])) for skill in skills_data)
        verified_skills = sum(1 for skill in skills_data if skill.get("verified", False))
        
        return {
            "user_id": user_id,
            "skill_coins": user.skill_coins,
            "experience_points": user.experience_points,
            "level": user.level,
            "sessions_taught": user.sessions_taught,
            "sessions_learned": user.sessions_learned,
            "average_rating": user.average_rating,
            "rating_count": user.rating_count,
            "total_skills": len(skills_data),
            "verified_skills": verified_skills,
            "total_endorsements": total_endorsements,
            "badges": len(user.badges),
            "member_since": user.created_at,
            "last_active": user.updated_at
        }
    
    async def get_leaderboard(self, category: str = "experience", limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard for different categories"""
        sort_field = {
            "experience": "experience_points",
            "sessions": "sessions_taught",
            "rating": "total_rating",
            "coins": "skill_coins"
        }.get(category, "experience_points")
        
        users_data = await self.users_collection.find(
            {"is_active": True}
        ).sort(sort_field, -1).limit(limit).to_list(None)
        
        leaderboard = []
        for idx, user_data in enumerate(users_data):
            user = User(**user_data)
            leaderboard.append({
                "rank": idx + 1,
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_image": user.profile_image,
                "level": user.level,
                "experience_points": user.experience_points,
                "sessions_taught": user.sessions_taught,
                "sessions_learned": user.sessions_learned,
                "average_rating": user.average_rating,
                "skill_coins": user.skill_coins,
                "badges": len(user.badges)
            })
        
        return leaderboard