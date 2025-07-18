from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from models import Skill, SkillCreate, SkillLevel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SkillService:
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.skills_collection = db.skills
        self.user_skills_collection = db.user_skills
        
    async def create_skill(self, skill_data: SkillCreate) -> Skill:
        """Create a new skill"""
        # Check if skill already exists
        existing_skill = await self.skills_collection.find_one({
            "name": {"$regex": f"^{skill_data.name}$", "$options": "i"}
        })
        
        if existing_skill:
            return Skill(**existing_skill)
        
        skill_dict = skill_data.dict()
        skill_dict["id"] = f"{skill_data.category}_{skill_data.name}".lower().replace(" ", "_")
        skill_dict["created_at"] = datetime.utcnow()
        skill_dict["popularity_score"] = 0.0
        skill_dict["is_active"] = True
        
        skill = Skill(**skill_dict)
        await self.skills_collection.insert_one(skill.dict())
        
        return skill
    
    async def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID"""
        skill_data = await self.skills_collection.find_one({"id": skill_id})
        if not skill_data:
            return None
        return Skill(**skill_data)
    
    async def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """Get skill by name"""
        skill_data = await self.skills_collection.find_one({
            "name": {"$regex": f"^{name}$", "$options": "i"}
        })
        if not skill_data:
            return None
        return Skill(**skill_data)
    
    async def search_skills(self, query: str, category: str = None, limit: int = 20) -> List[Skill]:
        """Search skills by name, category, or tags"""
        search_filter = {"is_active": True}
        
        if query:
            search_filter["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"tags": {"$regex": query, "$options": "i"}}
            ]
        
        if category:
            search_filter["category"] = {"$regex": category, "$options": "i"}
        
        skills_data = await self.skills_collection.find(search_filter).sort("popularity_score", -1).limit(limit).to_list(None)
        return [Skill(**skill) for skill in skills_data]
    
    async def get_all_skills(self, category: str = None, limit: int = 100) -> List[Skill]:
        """Get all skills, optionally filtered by category"""
        search_filter = {"is_active": True}
        
        if category:
            search_filter["category"] = category
        
        skills_data = await self.skills_collection.find(search_filter).sort("popularity_score", -1).limit(limit).to_list(None)
        return [Skill(**skill) for skill in skills_data]
    
    async def get_popular_skills(self, limit: int = 10) -> List[Skill]:
        """Get most popular skills"""
        skills_data = await self.skills_collection.find(
            {"is_active": True}
        ).sort("popularity_score", -1).limit(limit).to_list(None)
        return [Skill(**skill) for skill in skills_data]
    
    async def get_skill_categories(self) -> List[Dict[str, Any]]:
        """Get all skill categories with counts"""
        pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "subcategories": {"$addToSet": "$subcategory"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        categories = await self.skills_collection.aggregate(pipeline).to_list(None)
        return [
            {
                "category": cat["_id"],
                "count": cat["count"],
                "subcategories": [sub for sub in cat["subcategories"] if sub is not None]
            }
            for cat in categories
        ]
    
    async def update_skill_popularity(self, skill_id: str) -> bool:
        """Update skill popularity score based on usage"""
        # Count how many users have this skill
        user_count = await self.user_skills_collection.count_documents({"skill_id": skill_id})
        
        # Calculate popularity score (can be enhanced with more factors)
        popularity_score = user_count * 1.0  # Base score
        
        # Bonus for skills with endorsements
        endorsement_pipeline = [
            {"$match": {"skill_id": skill_id}},
            {"$project": {"endorsement_count": {"$size": "$endorsements"}}},
            {"$group": {"_id": None, "total_endorsements": {"$sum": "$endorsement_count"}}}
        ]
        
        endorsement_result = await self.user_skills_collection.aggregate(endorsement_pipeline).to_list(None)
        if endorsement_result:
            total_endorsements = endorsement_result[0]["total_endorsements"]
            popularity_score += total_endorsements * 0.5
        
        # Update skill popularity
        result = await self.skills_collection.update_one(
            {"id": skill_id},
            {"$set": {"popularity_score": popularity_score}}
        )
        
        return result.matched_count > 0
    
    async def get_skill_statistics(self, skill_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a skill"""
        skill_data = await self.skills_collection.find_one({"id": skill_id})
        if not skill_data:
            return {}
        
        skill = Skill(**skill_data)
        
        # Count users who have this skill
        user_count = await self.user_skills_collection.count_documents({"skill_id": skill_id})
        
        # Count by skill level
        level_pipeline = [
            {"$match": {"skill_id": skill_id}},
            {"$group": {"_id": "$level", "count": {"$sum": 1}}}
        ]
        level_stats = await self.user_skills_collection.aggregate(level_pipeline).to_list(None)
        level_distribution = {level["_id"]: level["count"] for level in level_stats}
        
        # Count total endorsements
        endorsement_pipeline = [
            {"$match": {"skill_id": skill_id}},
            {"$project": {"endorsement_count": {"$size": "$endorsements"}}},
            {"$group": {"_id": None, "total_endorsements": {"$sum": "$endorsement_count"}}}
        ]
        
        endorsement_result = await self.user_skills_collection.aggregate(endorsement_pipeline).to_list(None)
        total_endorsements = endorsement_result[0]["total_endorsements"] if endorsement_result else 0
        
        # Count verified skills
        verified_count = await self.user_skills_collection.count_documents({"skill_id": skill_id, "verified": True})
        
        return {
            "skill_id": skill_id,
            "name": skill.name,
            "category": skill.category,
            "total_users": user_count,
            "verified_users": verified_count,
            "total_endorsements": total_endorsements,
            "popularity_score": skill.popularity_score,
            "level_distribution": level_distribution,
            "created_at": skill.created_at
        }
    
    async def get_trending_skills(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending skills based on recent activity"""
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get skills added recently
        recent_skills_pipeline = [
            {"$match": {"created_at": {"$gte": cutoff_date}}},
            {"$group": {"_id": "$skill_id", "count": {"$sum": 1}, "skill_name": {"$first": "$skill_name"}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        trending_data = await self.user_skills_collection.aggregate(recent_skills_pipeline).to_list(None)
        
        trending_skills = []
        for item in trending_data:
            skill_data = await self.skills_collection.find_one({"id": item["_id"]})
            if skill_data:
                trending_skills.append({
                    "skill": Skill(**skill_data),
                    "recent_users": item["count"],
                    "growth_rate": item["count"] / days  # Users per day
                })
        
        return trending_skills
    
    async def suggest_skills(self, user_skills: List[str], limit: int = 5) -> List[Skill]:
        """Suggest skills based on user's current skills"""
        if not user_skills:
            return await self.get_popular_skills(limit)
        
        # Find users with similar skills
        similar_users_pipeline = [
            {"$match": {"skill_name": {"$in": user_skills}}},
            {"$group": {"_id": "$user_id", "common_skills": {"$sum": 1}}},
            {"$match": {"common_skills": {"$gte": 1}}},
            {"$sort": {"common_skills": -1}},
            {"$limit": 20}
        ]
        
        similar_users = await self.user_skills_collection.aggregate(similar_users_pipeline).to_list(None)
        similar_user_ids = [user["_id"] for user in similar_users]
        
        # Get skills from similar users that the current user doesn't have
        suggested_skills_pipeline = [
            {"$match": {
                "user_id": {"$in": similar_user_ids},
                "skill_name": {"$nin": user_skills}
            }},
            {"$group": {"_id": "$skill_id", "count": {"$sum": 1}, "skill_name": {"$first": "$skill_name"}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        suggested_data = await self.user_skills_collection.aggregate(suggested_skills_pipeline).to_list(None)
        
        suggested_skills = []
        for item in suggested_data:
            skill_data = await self.skills_collection.find_one({"id": item["_id"]})
            if skill_data:
                suggested_skills.append(Skill(**skill_data))
        
        # Fill remaining slots with popular skills if needed
        if len(suggested_skills) < limit:
            popular_skills = await self.get_popular_skills(limit - len(suggested_skills))
            for skill in popular_skills:
                if skill.name not in user_skills:
                    suggested_skills.append(skill)
        
        return suggested_skills[:limit]
    
    async def create_default_skills(self):
        """Create default skills for the platform"""
        default_skills = [
            # Programming
            {"name": "Python", "category": "Programming", "subcategory": "Backend", "tags": ["python", "backend", "programming"]},
            {"name": "JavaScript", "category": "Programming", "subcategory": "Frontend", "tags": ["javascript", "frontend", "web"]},
            {"name": "React", "category": "Programming", "subcategory": "Frontend", "tags": ["react", "frontend", "web", "javascript"]},
            {"name": "Node.js", "category": "Programming", "subcategory": "Backend", "tags": ["nodejs", "backend", "javascript"]},
            {"name": "HTML/CSS", "category": "Programming", "subcategory": "Frontend", "tags": ["html", "css", "frontend", "web"]},
            {"name": "SQL", "category": "Programming", "subcategory": "Database", "tags": ["sql", "database", "data"]},
            {"name": "Java", "category": "Programming", "subcategory": "Backend", "tags": ["java", "backend", "programming"]},
            {"name": "C++", "category": "Programming", "subcategory": "Systems", "tags": ["cpp", "systems", "programming"]},
            
            # Design
            {"name": "UI/UX Design", "category": "Design", "subcategory": "Digital", "tags": ["ui", "ux", "design", "user experience"]},
            {"name": "Photoshop", "category": "Design", "subcategory": "Graphics", "tags": ["photoshop", "graphics", "design"]},
            {"name": "Illustrator", "category": "Design", "subcategory": "Graphics", "tags": ["illustrator", "graphics", "design"]},
            {"name": "Figma", "category": "Design", "subcategory": "Digital", "tags": ["figma", "design", "prototyping"]},
            
            # Languages
            {"name": "Spanish", "category": "Languages", "subcategory": "European", "tags": ["spanish", "language", "communication"]},
            {"name": "French", "category": "Languages", "subcategory": "European", "tags": ["french", "language", "communication"]},
            {"name": "German", "category": "Languages", "subcategory": "European", "tags": ["german", "language", "communication"]},
            {"name": "Mandarin", "category": "Languages", "subcategory": "Asian", "tags": ["mandarin", "chinese", "language"]},
            {"name": "Japanese", "category": "Languages", "subcategory": "Asian", "tags": ["japanese", "language", "communication"]},
            
            # Business
            {"name": "Project Management", "category": "Business", "subcategory": "Management", "tags": ["project", "management", "business"]},
            {"name": "Marketing", "category": "Business", "subcategory": "Marketing", "tags": ["marketing", "business", "promotion"]},
            {"name": "Sales", "category": "Business", "subcategory": "Sales", "tags": ["sales", "business", "communication"]},
            {"name": "Data Analysis", "category": "Business", "subcategory": "Analytics", "tags": ["data", "analysis", "business"]},
            {"name": "Excel", "category": "Business", "subcategory": "Office", "tags": ["excel", "spreadsheet", "data"]},
            
            # Creative
            {"name": "Writing", "category": "Creative", "subcategory": "Content", "tags": ["writing", "content", "creative"]},
            {"name": "Photography", "category": "Creative", "subcategory": "Visual", "tags": ["photography", "visual", "art"]},
            {"name": "Video Editing", "category": "Creative", "subcategory": "Video", "tags": ["video", "editing", "creative"]},
            {"name": "Music Production", "category": "Creative", "subcategory": "Audio", "tags": ["music", "audio", "production"]},
            
            # Personal Development
            {"name": "Public Speaking", "category": "Personal Development", "subcategory": "Communication", "tags": ["speaking", "presentation", "communication"]},
            {"name": "Leadership", "category": "Personal Development", "subcategory": "Management", "tags": ["leadership", "management", "personal"]},
            {"name": "Time Management", "category": "Personal Development", "subcategory": "Productivity", "tags": ["time", "productivity", "personal"]},
            {"name": "Meditation", "category": "Personal Development", "subcategory": "Wellness", "tags": ["meditation", "wellness", "mindfulness"]},
            
            # Technical
            {"name": "Data Science", "category": "Technical", "subcategory": "Analytics", "tags": ["data", "science", "analytics"]},
            {"name": "Machine Learning", "category": "Technical", "subcategory": "AI", "tags": ["ml", "ai", "machine learning"]},
            {"name": "DevOps", "category": "Technical", "subcategory": "Operations", "tags": ["devops", "operations", "deployment"]},
            {"name": "Cybersecurity", "category": "Technical", "subcategory": "Security", "tags": ["security", "cyber", "protection"]},
        ]
        
        for skill_data in default_skills:
            skill_create = SkillCreate(**skill_data)
            await self.create_skill(skill_create)
        
        logger.info(f"Created {len(default_skills)} default skills")

from datetime import timedelta