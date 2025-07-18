import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import (
    Badge, UserBadge, Achievement, UserAchievement, LeaderboardEntry,
    SkillCoinTransaction, BadgeCreate, AchievementCreate, UserProgress,
    BadgeType, AchievementType
)
import uuid

logger = logging.getLogger(__name__)

class GamificationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.badges_collection = db.badges
        self.user_badges_collection = db.user_badges
        self.achievements_collection = db.achievements
        self.user_achievements_collection = db.user_achievements
        self.leaderboard_collection = db.leaderboard
        self.skill_coin_transactions_collection = db.skill_coin_transactions
        self.users_collection = db.users
        self.sessions_collection = db.sessions
        
    async def create_default_badges(self):
        """Create default badges for the system"""
        try:
            # Check if badges already exist
            existing_badges = await self.badges_collection.count_documents({})
            if existing_badges > 0:
                logger.info("Default badges already exist")
                return
            
            default_badges = [
                # Skill Master Badges
                Badge(
                    name="Skill Explorer",
                    description="Add your first skill to your profile",
                    badge_type=BadgeType.SKILL_MASTER,
                    color="#3B82F6",
                    requirements={"skills_added": 1},
                    skill_coins_reward=10
                ),
                Badge(
                    name="Multi-Skilled",
                    description="Master 5 different skills",
                    badge_type=BadgeType.SKILL_MASTER,
                    color="#3B82F6",
                    requirements={"skills_added": 5},
                    skill_coins_reward=50
                ),
                Badge(
                    name="Skill Virtuoso",
                    description="Master 10 different skills",
                    badge_type=BadgeType.SKILL_MASTER,
                    color="#8B5CF6",
                    requirements={"skills_added": 10},
                    skill_coins_reward=100
                ),
                
                # Mentor Badges
                Badge(
                    name="First Mentor",
                    description="Complete your first teaching session",
                    badge_type=BadgeType.MENTOR,
                    color="#10B981",
                    requirements={"teaching_sessions": 1},
                    skill_coins_reward=20
                ),
                Badge(
                    name="Experienced Mentor",
                    description="Complete 10 teaching sessions",
                    badge_type=BadgeType.MENTOR,
                    color="#10B981",
                    requirements={"teaching_sessions": 10},
                    skill_coins_reward=100
                ),
                Badge(
                    name="Master Mentor",
                    description="Complete 50 teaching sessions",
                    badge_type=BadgeType.MENTOR,
                    color="#F59E0B",
                    requirements={"teaching_sessions": 50},
                    skill_coins_reward=500
                ),
                
                # Learner Badges
                Badge(
                    name="Eager Learner",
                    description="Complete your first learning session",
                    badge_type=BadgeType.LEARNER,
                    color="#EC4899",
                    requirements={"learning_sessions": 1},
                    skill_coins_reward=15
                ),
                Badge(
                    name="Dedicated Student",
                    description="Complete 10 learning sessions",
                    badge_type=BadgeType.LEARNER,
                    color="#EC4899",
                    requirements={"learning_sessions": 10},
                    skill_coins_reward=75
                ),
                Badge(
                    name="Lifelong Learner",
                    description="Complete 50 learning sessions",
                    badge_type=BadgeType.LEARNER,
                    color="#DC2626",
                    requirements={"learning_sessions": 50},
                    skill_coins_reward=300
                ),
                
                # Social Badges
                Badge(
                    name="First Connection",
                    description="Send your first message",
                    badge_type=BadgeType.SOCIAL,
                    color="#6366F1",
                    requirements={"messages_sent": 1},
                    skill_coins_reward=5
                ),
                Badge(
                    name="Communicator",
                    description="Send 50 messages",
                    badge_type=BadgeType.SOCIAL,
                    color="#6366F1",
                    requirements={"messages_sent": 50},
                    skill_coins_reward=50
                ),
                Badge(
                    name="Community Builder",
                    description="Have conversations with 10 different users",
                    badge_type=BadgeType.SOCIAL,
                    color="#7C3AED",
                    requirements={"unique_conversations": 10},
                    skill_coins_reward=100
                ),
                
                # Milestone Badges
                Badge(
                    name="Welcome Aboard",
                    description="Complete your profile setup",
                    badge_type=BadgeType.MILESTONE,
                    color="#84CC16",
                    requirements={"profile_complete": True},
                    skill_coins_reward=25
                ),
                Badge(
                    name="Rising Star",
                    description="Earn 100 skill coins",
                    badge_type=BadgeType.MILESTONE,
                    color="#F97316",
                    requirements={"skill_coins_earned": 100},
                    skill_coins_reward=0
                ),
                Badge(
                    name="Skill Coin Collector",
                    description="Earn 1000 skill coins",
                    badge_type=BadgeType.MILESTONE,
                    color="#F97316",
                    requirements={"skill_coins_earned": 1000},
                    skill_coins_reward=100
                ),
                
                # Special Badges
                Badge(
                    name="5-Star Teacher",
                    description="Maintain a 5.0 average rating as a teacher",
                    badge_type=BadgeType.SPECIAL,
                    color="#FFD700",
                    requirements={"average_rating": 5.0, "teaching_sessions": 5},
                    skill_coins_reward=200
                ),
                Badge(
                    name="Consistency Champion",
                    description="Maintain a 7-day activity streak",
                    badge_type=BadgeType.SPECIAL,
                    color="#8B5CF6",
                    requirements={"activity_streak": 7},
                    skill_coins_reward=150
                ),
            ]
            
            # Insert all badges
            for badge in default_badges:
                await self.badges_collection.insert_one(badge.dict())
            
            logger.info(f"Created {len(default_badges)} default badges")
            
        except Exception as e:
            logger.error(f"Error creating default badges: {str(e)}")
            raise
    
    async def create_default_achievements(self):
        """Create default achievements for the system"""
        try:
            # Check if achievements already exist
            existing_achievements = await self.achievements_collection.count_documents({})
            if existing_achievements > 0:
                logger.info("Default achievements already exist")
                return
            
            default_achievements = [
                Achievement(
                    name="First Steps",
                    description="Complete your first skill-sharing session",
                    achievement_type=AchievementType.SESSIONS_COMPLETED,
                    color="#10B981",
                    requirements={"total_sessions": 1},
                    skill_coins_reward=30
                ),
                Achievement(
                    name="Session Veteran",
                    description="Complete 25 skill-sharing sessions",
                    achievement_type=AchievementType.SESSIONS_COMPLETED,
                    color="#10B981",
                    requirements={"total_sessions": 25},
                    skill_coins_reward=150
                ),
                Achievement(
                    name="Session Master",
                    description="Complete 100 skill-sharing sessions",
                    achievement_type=AchievementType.SESSIONS_COMPLETED,
                    color="#F59E0B",
                    requirements={"total_sessions": 100},
                    skill_coins_reward=500
                ),
                Achievement(
                    name="Skill Collector",
                    description="Add 3 different skills to your profile",
                    achievement_type=AchievementType.SKILL_EARNED,
                    color="#3B82F6",
                    requirements={"skills_count": 3},
                    skill_coins_reward=40
                ),
                Achievement(
                    name="Skill Arsenal",
                    description="Add 8 different skills to your profile",
                    achievement_type=AchievementType.SKILL_EARNED,
                    color="#8B5CF6",
                    requirements={"skills_count": 8},
                    skill_coins_reward=120
                ),
                Achievement(
                    name="Mentorship Milestone",
                    description="Complete 20 teaching sessions",
                    achievement_type=AchievementType.MENTORING_MILESTONE,
                    color="#10B981",
                    requirements={"teaching_sessions": 20},
                    skill_coins_reward=200
                ),
                Achievement(
                    name="Learning Champion",
                    description="Complete 20 learning sessions",
                    achievement_type=AchievementType.LEARNING_MILESTONE,
                    color="#EC4899",
                    requirements={"learning_sessions": 20},
                    skill_coins_reward=180
                ),
                Achievement(
                    name="Social Butterfly",
                    description="Start conversations with 5 different users",
                    achievement_type=AchievementType.SOCIAL_MILESTONE,
                    color="#6366F1",
                    requirements={"unique_conversations": 5},
                    skill_coins_reward=80
                ),
                Achievement(
                    name="Highly Rated",
                    description="Maintain an average rating of 4.5 or higher",
                    achievement_type=AchievementType.RATING_MILESTONE,
                    color="#F59E0B",
                    requirements={"average_rating": 4.5, "total_sessions": 10},
                    skill_coins_reward=250
                ),
                Achievement(
                    name="Streak Keeper",
                    description="Maintain a 14-day activity streak",
                    achievement_type=AchievementType.STREAK_MILESTONE,
                    color="#8B5CF6",
                    requirements={"activity_streak": 14},
                    skill_coins_reward=300
                ),
            ]
            
            # Insert all achievements
            for achievement in default_achievements:
                await self.achievements_collection.insert_one(achievement.dict())
            
            logger.info(f"Created {len(default_achievements)} default achievements")
            
        except Exception as e:
            logger.error(f"Error creating default achievements: {str(e)}")
            raise
    
    async def get_user_progress(self, user_id: str) -> Optional[UserProgress]:
        """Get comprehensive progress for a user"""
        try:
            # Get user data
            user = await self.users_collection.find_one({"id": user_id})
            if not user:
                return None
            
            # Get user badges
            user_badges = await self.user_badges_collection.find({"user_id": user_id}).to_list(100)
            badges = [UserBadge(**badge) for badge in user_badges]
            
            # Get user achievements
            user_achievements = await self.user_achievements_collection.find({"user_id": user_id}).to_list(100)
            achievements = [UserAchievement(**achievement) for achievement in user_achievements]
            
            # Get session statistics
            sessions = await self.sessions_collection.find({
                "$or": [{"teacher_id": user_id}, {"learner_id": user_id}]
            }).to_list(1000)
            
            total_sessions = len(sessions)
            teaching_sessions = len([s for s in sessions if s.get("teacher_id") == user_id])
            learning_sessions = len([s for s in sessions if s.get("learner_id") == user_id])
            
            # Calculate average rating
            ratings = [s.get("rating", 0) for s in sessions if s.get("rating")]
            average_rating = sum(ratings) / len(ratings) if ratings else 0.0
            
            # Get leaderboard position
            leaderboard_entry = await self.leaderboard_collection.find_one({"user_id": user_id})
            leaderboard_rank = leaderboard_entry.get("rank", 0) if leaderboard_entry else 0
            
            return UserProgress(
                user_id=user_id,
                skill_coins=user.get("skill_coins", 0),
                total_sessions=total_sessions,
                teaching_sessions=teaching_sessions,
                learning_sessions=learning_sessions,
                average_rating=average_rating,
                badges=badges,
                achievements=achievements,
                current_streak=user.get("current_streak", 0),
                longest_streak=user.get("longest_streak", 0),
                leaderboard_rank=leaderboard_rank,
                recent_activities=user.get("recent_activities", [])
            )
            
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            return None
    
    async def award_skill_coins(self, user_id: str, amount: int, transaction_type: str, source: str, source_id: str = None, description: str = "") -> bool:
        """Award skill coins to a user"""
        try:
            # Get current user balance
            user = await self.users_collection.find_one({"id": user_id})
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            current_balance = user.get("skill_coins", 0)
            new_balance = current_balance + amount
            
            # Update user balance
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": {"skill_coins": new_balance}}
            )
            
            # Create transaction record
            transaction = SkillCoinTransaction(
                user_id=user_id,
                amount=amount,
                transaction_type=transaction_type,
                source=source,
                source_id=source_id,
                description=description,
                balance_after=new_balance
            )
            
            await self.skill_coin_transactions_collection.insert_one(transaction.dict())
            
            logger.info(f"Awarded {amount} skill coins to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error awarding skill coins: {str(e)}")
            return False
    
    async def check_and_award_badges(self, user_id: str) -> List[Badge]:
        """Check user progress and award any earned badges"""
        try:
            awarded_badges = []
            
            # Get user progress
            progress = await self.get_user_progress(user_id)
            if not progress:
                return awarded_badges
            
            # Get all available badges
            all_badges = await self.badges_collection.find({"is_active": True}).to_list(100)
            
            # Get already earned badges
            earned_badge_ids = [ub.badge_id for ub in progress.badges]
            
            for badge_data in all_badges:
                badge = Badge(**badge_data)
                
                # Skip if already earned
                if badge.id in earned_badge_ids:
                    continue
                
                # Check if requirements are met
                if await self._check_badge_requirements(user_id, badge, progress):
                    # Award badge
                    user_badge = UserBadge(
                        user_id=user_id,
                        badge_id=badge.id
                    )
                    
                    await self.user_badges_collection.insert_one(user_badge.dict())
                    
                    # Award skill coins if any
                    if badge.skill_coins_reward > 0:
                        await self.award_skill_coins(
                            user_id=user_id,
                            amount=badge.skill_coins_reward,
                            transaction_type="earned",
                            source="badge",
                            source_id=badge.id,
                            description=f"Badge reward: {badge.name}"
                        )
                    
                    awarded_badges.append(badge)
                    logger.info(f"Awarded badge '{badge.name}' to user {user_id}")
            
            return awarded_badges
            
        except Exception as e:
            logger.error(f"Error checking and awarding badges: {str(e)}")
            return []
    
    async def _check_badge_requirements(self, user_id: str, badge: Badge, progress: UserProgress) -> bool:
        """Check if user meets badge requirements"""
        try:
            requirements = badge.requirements
            
            # Check each requirement
            for req_key, req_value in requirements.items():
                if req_key == "skills_added":
                    user_skills = await self.db.user_skills.count_documents({"user_id": user_id})
                    if user_skills < req_value:
                        return False
                
                elif req_key == "teaching_sessions":
                    if progress.teaching_sessions < req_value:
                        return False
                
                elif req_key == "learning_sessions":
                    if progress.learning_sessions < req_value:
                        return False
                
                elif req_key == "messages_sent":
                    messages_count = await self.db.messages.count_documents({"sender_id": user_id})
                    if messages_count < req_value:
                        return False
                
                elif req_key == "unique_conversations":
                    conversations_count = await self.db.conversations.count_documents({"participants": user_id})
                    if conversations_count < req_value:
                        return False
                
                elif req_key == "profile_complete":
                    user = await self.users_collection.find_one({"id": user_id})
                    if not user or not user.get("bio") or not user.get("location"):
                        return False
                
                elif req_key == "skill_coins_earned":
                    if progress.skill_coins < req_value:
                        return False
                
                elif req_key == "average_rating":
                    if progress.average_rating < req_value:
                        return False
                
                elif req_key == "activity_streak":
                    if progress.current_streak < req_value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking badge requirements: {str(e)}")
            return False
    
    async def get_leaderboard(self, limit: int = 50) -> List[LeaderboardEntry]:
        """Get the current leaderboard"""
        try:
            # Update leaderboard data
            await self.update_leaderboard()
            
            # Get leaderboard entries
            entries = await self.leaderboard_collection.find().sort("rank", 1).limit(limit).to_list(limit)
            
            return [LeaderboardEntry(**entry) for entry in entries]
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {str(e)}")
            return []
    
    async def update_leaderboard(self):
        """Update the leaderboard with current user statistics"""
        try:
            # Get all users
            users = await self.users_collection.find({"is_active": True}).to_list(1000)
            
            leaderboard_entries = []
            
            for user in users:
                user_id = user["id"]
                
                # Get user progress
                progress = await self.get_user_progress(user_id)
                if not progress:
                    continue
                
                # Get badge and achievement counts
                badges_count = len(progress.badges)
                achievements_count = len(progress.achievements)
                
                # Create leaderboard entry
                entry = LeaderboardEntry(
                    user_id=user_id,
                    username=user["username"],
                    skill_coins=progress.skill_coins,
                    total_sessions=progress.total_sessions,
                    teaching_sessions=progress.teaching_sessions,
                    learning_sessions=progress.learning_sessions,
                    average_rating=progress.average_rating,
                    badges_count=badges_count,
                    achievements_count=achievements_count,
                    current_streak=progress.current_streak,
                    longest_streak=progress.longest_streak,
                    last_active=user.get("updated_at", datetime.utcnow())
                )
                
                leaderboard_entries.append(entry)
            
            # Sort by skill coins (primary) and total sessions (secondary)
            leaderboard_entries.sort(key=lambda x: (x.skill_coins, x.total_sessions), reverse=True)
            
            # Assign ranks
            for i, entry in enumerate(leaderboard_entries):
                entry.rank = i + 1
            
            # Clear existing leaderboard
            await self.leaderboard_collection.delete_many({})
            
            # Insert new leaderboard
            if leaderboard_entries:
                await self.leaderboard_collection.insert_many([entry.dict() for entry in leaderboard_entries])
            
            logger.info(f"Updated leaderboard with {len(leaderboard_entries)} entries")
            
        except Exception as e:
            logger.error(f"Error updating leaderboard: {str(e)}")
            raise
    
    async def get_all_badges(self) -> List[Badge]:
        """Get all available badges"""
        try:
            badges = await self.badges_collection.find({"is_active": True}).to_list(100)
            return [Badge(**badge) for badge in badges]
        except Exception as e:
            logger.error(f"Error getting all badges: {str(e)}")
            return []
    
    async def get_all_achievements(self) -> List[Achievement]:
        """Get all available achievements"""
        try:
            achievements = await self.achievements_collection.find({"is_active": True}).to_list(100)
            return [Achievement(**achievement) for achievement in achievements]
        except Exception as e:
            logger.error(f"Error getting all achievements: {str(e)}")
            return []
    
    async def get_user_transactions(self, user_id: str, limit: int = 50) -> List[SkillCoinTransaction]:
        """Get user's skill coin transaction history"""
        try:
            transactions = await self.skill_coin_transactions_collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit).to_list(limit)
            
            return [SkillCoinTransaction(**transaction) for transaction in transactions]
            
        except Exception as e:
            logger.error(f"Error getting user transactions: {str(e)}")
            return []