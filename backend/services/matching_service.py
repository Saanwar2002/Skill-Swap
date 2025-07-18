from typing import List, Dict, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorClient
from models import User, UserResponse, Match, MatchFilters
from datetime import datetime, timedelta
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import logging
import math

logger = logging.getLogger(__name__)

class MatchingService:
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.users_collection = db.users
        self.matches_collection = db.matches
        self.user_skills_collection = db.user_skills
        self.sessions_collection = db.sessions
        
    async def find_matches(self, user_id: str, filters: MatchFilters = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Find potential matches for a user using AI-powered algorithm"""
        # Get user profile
        user_data = await self.users_collection.find_one({"id": user_id})
        if not user_data:
            return []
        
        user = User(**user_data)
        
        # Get all potential matches
        potential_matches = await self._get_potential_matches(user, filters)
        
        # Calculate compatibility scores
        matches_with_scores = []
        for match_user in potential_matches:
            score = await self._calculate_compatibility_score(user, match_user)
            if score > 0.1:  # Minimum threshold
                matches_with_scores.append({
                    "user": match_user,
                    "compatibility_score": score,
                    "match_reasons": await self._get_match_reasons(user, match_user)
                })
        
        # Sort by compatibility score
        matches_with_scores.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        # Save matches to database
        await self._save_matches(user_id, matches_with_scores[:limit])
        
        return matches_with_scores[:limit]
    
    async def _get_potential_matches(self, user: User, filters: MatchFilters = None) -> List[User]:
        """Get potential matches based on basic criteria"""
        search_filter = {
            "id": {"$ne": user.id},
            "is_active": True
        }
        
        # User wants to learn skills that others offer
        if user.skills_wanted:
            search_filter["skills_offered"] = {"$in": user.skills_wanted}
        
        # User offers skills that others want
        if user.skills_offered:
            search_filter["$or"] = [
                {"skills_wanted": {"$in": user.skills_offered}},
                {"skills_offered": {"$in": user.skills_wanted}}
            ]
        
        # Apply filters
        if filters:
            if filters.skills_offered:
                search_filter["skills_offered"] = {"$in": filters.skills_offered}
            if filters.skills_wanted:
                search_filter["skills_wanted"] = {"$in": filters.skills_wanted}
            if filters.location:
                search_filter["location"] = {"$regex": filters.location, "$options": "i"}
            if filters.min_rating:
                search_filter["$expr"] = {
                    "$gte": [
                        {"$cond": [{"$eq": ["$rating_count", 0]}, 0, {"$divide": ["$total_rating", "$rating_count"]}]},
                        filters.min_rating
                    ]
                }
            if filters.languages:
                search_filter["languages"] = {"$in": filters.languages}
        
        users_data = await self.users_collection.find(search_filter).to_list(100)
        return [User(**user_data) for user_data in users_data]
    
    async def _calculate_compatibility_score(self, user1: User, user2: User) -> float:
        """Calculate compatibility score between two users using multiple factors"""
        factors = {}
        
        # 1. Skill Match Score (40% weight)
        skill_score = self._calculate_skill_match_score(user1, user2)
        factors["skill_match"] = skill_score
        
        # 2. Experience Level Compatibility (20% weight)
        experience_score = await self._calculate_experience_compatibility(user1, user2)
        factors["experience_compatibility"] = experience_score
        
        # 3. Location Compatibility (10% weight)
        location_score = self._calculate_location_compatibility(user1, user2)
        factors["location_compatibility"] = location_score
        
        # 4. Language Compatibility (10% weight)
        language_score = self._calculate_language_compatibility(user1, user2)
        factors["language_compatibility"] = language_score
        
        # 5. Availability Overlap (10% weight)
        availability_score = self._calculate_availability_overlap(user1, user2)
        factors["availability_overlap"] = availability_score
        
        # 6. Reputation Score (10% weight)
        reputation_score = self._calculate_reputation_score(user1, user2)
        factors["reputation_score"] = reputation_score
        
        # Calculate weighted score
        weights = {
            "skill_match": 0.4,
            "experience_compatibility": 0.2,
            "location_compatibility": 0.1,
            "language_compatibility": 0.1,
            "availability_overlap": 0.1,
            "reputation_score": 0.1
        }
        
        total_score = sum(factors[factor] * weights[factor] for factor in factors)
        
        return min(1.0, max(0.0, total_score))
    
    def _calculate_skill_match_score(self, user1: User, user2: User) -> float:
        """Calculate skill compatibility score"""
        # Skills user1 wants that user2 offers
        user1_wants_user2_offers = set(user1.skills_wanted) & set(user2.skills_offered)
        
        # Skills user2 wants that user1 offers
        user2_wants_user1_offers = set(user2.skills_wanted) & set(user1.skills_offered)
        
        # Calculate bidirectional match score
        if not user1.skills_wanted and not user2.skills_wanted:
            return 0.0
        
        max_possible_matches = max(len(user1.skills_wanted), len(user2.skills_wanted))
        actual_matches = len(user1_wants_user2_offers) + len(user2_wants_user1_offers)
        
        if max_possible_matches == 0:
            return 0.0
        
        base_score = actual_matches / max_possible_matches
        
        # Bonus for bidirectional matches
        if user1_wants_user2_offers and user2_wants_user1_offers:
            base_score *= 1.5
        
        return min(1.0, base_score)
    
    async def _calculate_experience_compatibility(self, user1: User, user2: User) -> float:
        """Calculate experience level compatibility"""
        # Get user skills with levels
        user1_skills = await self.user_skills_collection.find({"user_id": user1.id}).to_list(None)
        user2_skills = await self.user_skills_collection.find({"user_id": user2.id}).to_list(None)
        
        if not user1_skills or not user2_skills:
            return 0.5  # Neutral score
        
        # Create skill level mapping
        level_values = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}
        
        user1_skill_levels = {skill["skill_name"]: level_values.get(skill["level"], 1) for skill in user1_skills}
        user2_skill_levels = {skill["skill_name"]: level_values.get(skill["level"], 1) for skill in user2_skills}
        
        # Calculate compatibility for overlapping skills
        common_skills = set(user1_skill_levels.keys()) & set(user2_skill_levels.keys())
        
        if not common_skills:
            return 0.7  # Good score for different skill sets
        
        compatibility_scores = []
        for skill in common_skills:
            level_diff = abs(user1_skill_levels[skill] - user2_skill_levels[skill])
            # Prefer 1-2 level differences for good teaching/learning dynamics
            if level_diff == 1:
                compatibility_scores.append(1.0)
            elif level_diff == 2:
                compatibility_scores.append(0.8)
            elif level_diff == 0:
                compatibility_scores.append(0.6)
            else:
                compatibility_scores.append(0.3)
        
        return sum(compatibility_scores) / len(compatibility_scores)
    
    def _calculate_location_compatibility(self, user1: User, user2: User) -> float:
        """Calculate location compatibility"""
        if not user1.location or not user2.location:
            return 0.5  # Neutral score for missing location
        
        # Simple text similarity for location
        location1 = user1.location.lower()
        location2 = user2.location.lower()
        
        if location1 == location2:
            return 1.0
        
        # Check for partial matches (city, state, country)
        location1_parts = set(location1.split())
        location2_parts = set(location2.split())
        
        common_parts = location1_parts & location2_parts
        if common_parts:
            return len(common_parts) / max(len(location1_parts), len(location2_parts))
        
        return 0.2  # Low score for different locations
    
    def _calculate_language_compatibility(self, user1: User, user2: User) -> float:
        """Calculate language compatibility"""
        if not user1.languages or not user2.languages:
            return 0.5  # Neutral score for missing languages
        
        common_languages = set(user1.languages) & set(user2.languages)
        if not common_languages:
            return 0.1  # Low score for no common languages
        
        return len(common_languages) / max(len(user1.languages), len(user2.languages))
    
    def _calculate_availability_overlap(self, user1: User, user2: User) -> float:
        """Calculate availability overlap"""
        if not user1.availability or not user2.availability:
            return 0.5  # Neutral score for missing availability
        
        # Simple availability overlap calculation
        # This can be enhanced with more sophisticated time zone and schedule analysis
        common_days = set(user1.availability.keys()) & set(user2.availability.keys())
        
        if not common_days:
            return 0.0
        
        return len(common_days) / 7  # Assuming 7 days of the week
    
    def _calculate_reputation_score(self, user1: User, user2: User) -> float:
        """Calculate reputation-based compatibility"""
        # Prefer users with good ratings
        user1_rating = user1.average_rating if user1.rating_count > 0 else 3.0
        user2_rating = user2.average_rating if user2.rating_count > 0 else 3.0
        
        # Normalize ratings to 0-1 scale
        user1_norm = (user1_rating - 1) / 4
        user2_norm = (user2_rating - 1) / 4
        
        # Average of both ratings
        return (user1_norm + user2_norm) / 2
    
    async def _get_match_reasons(self, user1: User, user2: User) -> List[str]:
        """Generate reasons for the match"""
        reasons = []
        
        # Skill matches
        user1_wants_user2_offers = set(user1.skills_wanted) & set(user2.skills_offered)
        user2_wants_user1_offers = set(user2.skills_wanted) & set(user1.skills_offered)
        
        if user1_wants_user2_offers:
            skills_str = ", ".join(user1_wants_user2_offers)
            reasons.append(f"They can teach you: {skills_str}")
        
        if user2_wants_user1_offers:
            skills_str = ", ".join(user2_wants_user1_offers)
            reasons.append(f"You can teach them: {skills_str}")
        
        # Location
        if user1.location and user2.location and user1.location.lower() == user2.location.lower():
            reasons.append(f"You're both in {user1.location}")
        
        # Languages
        common_languages = set(user1.languages) & set(user2.languages)
        if common_languages:
            languages_str = ", ".join(common_languages)
            reasons.append(f"Common languages: {languages_str}")
        
        # High rating
        if user2.average_rating >= 4.5 and user2.rating_count >= 5:
            reasons.append("Highly rated teacher")
        
        # Experience level
        if user2.sessions_taught > 10:
            reasons.append("Experienced teacher")
        
        return reasons
    
    async def _save_matches(self, user_id: str, matches: List[Dict[str, Any]]):
        """Save matches to database"""
        for match_data in matches:
            match_user = match_data["user"]
            
            # Check if match already exists
            existing_match = await self.matches_collection.find_one({
                "$or": [
                    {"user1_id": user_id, "user2_id": match_user.id},
                    {"user1_id": match_user.id, "user2_id": user_id}
                ]
            })
            
            if not existing_match:
                # Create new match
                match = Match(
                    user1_id=user_id,
                    user2_id=match_user.id,
                    skill_offered=", ".join(match_user.skills_offered[:3]),
                    skill_wanted=", ".join(match_user.skills_wanted[:3]),
                    compatibility_score=match_data["compatibility_score"],
                    algorithm_data={
                        "match_reasons": match_data["match_reasons"],
                        "created_by": "ai_matching",
                        "version": "1.0"
                    }
                )
                
                await self.matches_collection.insert_one(match.dict())
    
    async def get_user_matches(self, user_id: str, status: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get matches for a user"""
        match_filter = {
            "$or": [
                {"user1_id": user_id},
                {"user2_id": user_id}
            ]
        }
        
        if status:
            match_filter["status"] = status
        
        matches_data = await self.matches_collection.find(match_filter).sort("compatibility_score", -1).limit(limit).to_list(None)
        
        result = []
        for match_data in matches_data:
            match = Match(**match_data)
            
            # Get the other user's profile
            other_user_id = match.user2_id if match.user1_id == user_id else match.user1_id
            other_user_data = await self.users_collection.find_one({"id": other_user_id})
            
            if other_user_data:
                other_user_obj = User(**other_user_data)
                other_user = UserResponse(**other_user_obj.dict(), average_rating=other_user_obj.average_rating)
                result.append({
                    "match": match,
                    "user": other_user,
                    "match_reasons": match.algorithm_data.get("match_reasons", [])
                })
        
        return result
    
    async def update_match_interest(self, match_id: str, user_id: str, interested: bool) -> bool:
        """Update user interest in a match"""
        match_data = await self.matches_collection.find_one({"id": match_id})
        if not match_data:
            return False
        
        match = Match(**match_data)
        
        # Update interest based on which user is responding
        if match.user1_id == user_id:
            update_data = {"user1_interest": interested}
        elif match.user2_id == user_id:
            update_data = {"user2_interest": interested}
        else:
            return False
        
        # Check if both users are interested
        if interested:
            current_match = await self.matches_collection.find_one({"id": match_id})
            if current_match:
                if (match.user1_id == user_id and current_match.get("user2_interest", False)) or \
                   (match.user2_id == user_id and current_match.get("user1_interest", False)):
                    update_data["status"] = "accepted"
        else:
            update_data["status"] = "declined"
        
        result = await self.matches_collection.update_one(
            {"id": match_id},
            {"$set": update_data}
        )
        
        return result.matched_count > 0
    
    async def get_match_suggestions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get AI-powered match suggestions"""
        # Use collaborative filtering to find similar users
        user_data = await self.users_collection.find_one({"id": user_id})
        if not user_data:
            return []
        
        user = User(**user_data)
        
        # Find users with similar skill interests
        similar_users = await self._find_similar_users(user)
        
        # Get their connections and suggest new matches
        suggestions = []
        for similar_user in similar_users:
            # Get matches of similar users
            similar_matches = await self.matches_collection.find({
                "$or": [
                    {"user1_id": similar_user.id},
                    {"user2_id": similar_user.id}
                ],
                "status": "accepted"
            }).to_list(None)
            
            for match_data in similar_matches:
                match = Match(**match_data)
                other_user_id = match.user2_id if match.user1_id == similar_user.id else match.user1_id
                
                # Don't suggest the user themselves or existing matches
                if other_user_id != user_id:
                    existing_match = await self.matches_collection.find_one({
                        "$or": [
                            {"user1_id": user_id, "user2_id": other_user_id},
                            {"user1_id": other_user_id, "user2_id": user_id}
                        ]
                    })
                    
                    if not existing_match:
                        other_user_data = await self.users_collection.find_one({"id": other_user_id})
                        if other_user_data:
                            other_user = User(**other_user_data)
                            compatibility = await self._calculate_compatibility_score(user, other_user)
                            
                            suggestions.append({
                                "user": UserResponse(**other_user.dict()),
                                "compatibility_score": compatibility,
                                "suggestion_reason": f"Users with similar interests also matched with this person"
                            })
        
        # Remove duplicates and sort by compatibility
        seen_users = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion["user"].id not in seen_users:
                seen_users.add(suggestion["user"].id)
                unique_suggestions.append(suggestion)
        
        unique_suggestions.sort(key=lambda x: x["compatibility_score"], reverse=True)
        return unique_suggestions[:limit]
    
    async def _find_similar_users(self, user: User, limit: int = 20) -> List[User]:
        """Find users with similar skill profiles"""
        # Simple similarity based on skill overlap
        user_skills = set(user.skills_offered + user.skills_wanted)
        
        if not user_skills:
            return []
        
        # Find users with overlapping skills
        similar_users_data = await self.users_collection.find({
            "id": {"$ne": user.id},
            "is_active": True,
            "$or": [
                {"skills_offered": {"$in": list(user_skills)}},
                {"skills_wanted": {"$in": list(user_skills)}}
            ]
        }).limit(limit).to_list(None)
        
        return [User(**user_data) for user_data in similar_users_data]
    
    async def get_matching_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics for user's matching activity"""
        # Get all matches for user
        matches = await self.matches_collection.find({
            "$or": [
                {"user1_id": user_id},
                {"user2_id": user_id}
            ]
        }).to_list(None)
        
        total_matches = len(matches)
        accepted_matches = len([m for m in matches if m["status"] == "accepted"])
        pending_matches = len([m for m in matches if m["status"] == "pending"])
        declined_matches = len([m for m in matches if m["status"] == "declined"])
        
        # Calculate average compatibility score
        if total_matches > 0:
            avg_compatibility = sum(m["compatibility_score"] for m in matches) / total_matches
        else:
            avg_compatibility = 0.0
        
        return {
            "total_matches": total_matches,
            "accepted_matches": accepted_matches,
            "pending_matches": pending_matches,
            "declined_matches": declined_matches,
            "acceptance_rate": accepted_matches / total_matches if total_matches > 0 else 0.0,
            "average_compatibility": avg_compatibility,
            "last_match_date": max([m["created_at"] for m in matches]) if matches else None
        }