from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from models import Session, SessionStatus, User, UserResponse
from datetime import datetime, timedelta
from services.user_service import UserService
import logging
import uuid

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.sessions_collection = db.sessions
        self.users_collection = db.users
        self.user_service = UserService(db)
    
    async def create_session(self, teacher_id: str, learner_id: str, session_data: Dict[str, Any]) -> Optional[Session]:
        """Create a new session"""
        try:
            # Validate users exist
            teacher = await self.users_collection.find_one({"id": teacher_id})
            learner = await self.users_collection.find_one({"id": learner_id})
            
            if not teacher or not learner:
                raise ValueError("Teacher or learner not found")
            
            # Create session
            session = Session(
                id=str(uuid.uuid4()),
                teacher_id=teacher_id,
                learner_id=learner_id,
                skill_id=session_data["skill_id"],
                skill_name=session_data["skill_name"],
                title=session_data["title"],
                description=session_data.get("description"),
                scheduled_start=session_data["scheduled_start"],
                scheduled_end=session_data["scheduled_end"],
                timezone=session_data.get("timezone", "UTC"),
                session_type=session_data.get("session_type", "video"),
                learning_objectives=session_data.get("learning_objectives", []),
                skill_coins_paid=session_data.get("skill_coins_paid", 0),
                status=SessionStatus.SCHEDULED
            )
            
            # Insert into database
            await self.sessions_collection.insert_one(session.dict())
            
            # Update user statistics
            await self.user_service.update_user_sessions(teacher_id, "taught")
            await self.user_service.update_user_sessions(learner_id, "learned")
            
            return session
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return None
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        try:
            session_data = await self.sessions_collection.find_one({"id": session_id})
            if session_data:
                return Session(**session_data)
            return None
        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            return None
    
    async def update_session(self, session_id: str, update_data: Dict[str, Any]) -> Optional[Session]:
        """Update session"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.sessions_collection.update_one(
                {"id": session_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_session(session_id)
            return None
            
        except Exception as e:
            logger.error(f"Error updating session: {str(e)}")
            return None
    
    async def get_user_sessions(self, user_id: str, role: str = "all", status: str = "all", limit: int = 50) -> List[Session]:
        """Get sessions for a user"""
        try:
            query = {}
            
            # Filter by role
            if role == "teacher":
                query["teacher_id"] = user_id
            elif role == "learner":
                query["learner_id"] = user_id
            else:
                query["$or"] = [{"teacher_id": user_id}, {"learner_id": user_id}]
            
            # Filter by status
            if status != "all":
                query["status"] = status
            
            cursor = self.sessions_collection.find(query).sort("scheduled_start", -1).limit(limit)
            sessions = []
            
            async for session_data in cursor:
                sessions.append(Session(**session_data))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return []
    
    async def get_upcoming_sessions(self, user_id: str, limit: int = 20) -> List[Session]:
        """Get upcoming sessions for a user"""
        try:
            now = datetime.utcnow()
            query = {
                "$or": [{"teacher_id": user_id}, {"learner_id": user_id}],
                "scheduled_start": {"$gt": now},
                "status": {"$in": ["scheduled", "in_progress"]}
            }
            
            cursor = self.sessions_collection.find(query).sort("scheduled_start", 1).limit(limit)
            sessions = []
            
            async for session_data in cursor:
                sessions.append(Session(**session_data))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting upcoming sessions: {str(e)}")
            return []
    
    async def cancel_session(self, session_id: str, user_id: str, reason: str = None) -> bool:
        """Cancel a session"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Check if user is participant
            if session.teacher_id != user_id and session.learner_id != user_id:
                return False
            
            # Update session status
            update_data = {
                "status": SessionStatus.CANCELLED,
                "notes": f"Cancelled by user. Reason: {reason}" if reason else "Cancelled by user"
            }
            
            result = await self.sessions_collection.update_one(
                {"id": session_id},
                {"$set": update_data}
            )
            
            # Refund skill coins if applicable
            if session.skill_coins_paid > 0:
                await self.refund_skill_coins(session)
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error cancelling session: {str(e)}")
            return False
    
    async def start_session(self, session_id: str, user_id: str) -> bool:
        """Mark session as started"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Check if user is participant
            if session.teacher_id != user_id and session.learner_id != user_id:
                return False
            
            # Update session status
            update_data = {
                "status": SessionStatus.IN_PROGRESS,
                "actual_start": datetime.utcnow()
            }
            
            result = await self.sessions_collection.update_one(
                {"id": session_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error starting session: {str(e)}")
            return False
    
    async def end_session(self, session_id: str, user_id: str) -> bool:
        """Mark session as completed"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Check if user is participant
            if session.teacher_id != user_id and session.learner_id != user_id:
                return False
            
            # Update session status
            update_data = {
                "status": SessionStatus.COMPLETED,
                "actual_end": datetime.utcnow()
            }
            
            result = await self.sessions_collection.update_one(
                {"id": session_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            return False
    
    async def submit_session_feedback(self, session_id: str, user_id: str, rating: float, feedback: str) -> bool:
        """Submit session feedback and rating"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Check if user is participant
            if session.teacher_id != user_id and session.learner_id != user_id:
                return False
            
            # Determine if user is teacher or learner
            if session.teacher_id == user_id:
                update_data = {
                    "teacher_rating": rating,
                    "teacher_feedback": feedback
                }
                # Update learner's rating
                await self.user_service.update_user_rating(session.learner_id, rating)
            else:
                update_data = {
                    "learner_rating": rating,
                    "learner_feedback": feedback
                }
                # Update teacher's rating
                await self.user_service.update_user_rating(session.teacher_id, rating)
            
            result = await self.sessions_collection.update_one(
                {"id": session_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            return False
    
    async def get_session_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get session statistics for a user"""
        try:
            # Get all sessions for the user
            sessions = await self.get_user_sessions(user_id)
            
            # Calculate statistics
            total_sessions = len(sessions)
            sessions_as_teacher = len([s for s in sessions if s.teacher_id == user_id])
            sessions_as_learner = len([s for s in sessions if s.learner_id == user_id])
            completed_sessions = len([s for s in sessions if s.status == SessionStatus.COMPLETED])
            cancelled_sessions = len([s for s in sessions if s.status == SessionStatus.CANCELLED])
            
            # Calculate total hours
            total_hours = 0
            for session in sessions:
                if session.actual_start and session.actual_end:
                    duration = session.actual_end - session.actual_start
                    total_hours += duration.total_seconds() / 3600
                elif session.scheduled_start and session.scheduled_end:
                    duration = session.scheduled_end - session.scheduled_start
                    total_hours += duration.total_seconds() / 3600
            
            # Calculate average ratings
            teacher_ratings = [s.teacher_rating for s in sessions if s.teacher_rating and s.teacher_id == user_id]
            learner_ratings = [s.learner_rating for s in sessions if s.learner_rating and s.learner_id == user_id]
            
            return {
                "total_sessions": total_sessions,
                "sessions_as_teacher": sessions_as_teacher,
                "sessions_as_learner": sessions_as_learner,
                "completed_sessions": completed_sessions,
                "cancelled_sessions": cancelled_sessions,
                "total_hours": round(total_hours, 2),
                "average_teacher_rating": round(sum(teacher_ratings) / len(teacher_ratings), 2) if teacher_ratings else 0,
                "average_learner_rating": round(sum(learner_ratings) / len(learner_ratings), 2) if learner_ratings else 0,
                "completion_rate": round(completed_sessions / total_sessions * 100, 2) if total_sessions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting session statistics: {str(e)}")
            return {}
    
    async def refund_skill_coins(self, session: Session) -> bool:
        """Refund skill coins for cancelled session"""
        try:
            # Add coins back to learner
            await self.users_collection.update_one(
                {"id": session.learner_id},
                {"$inc": {"skill_coins": session.skill_coins_paid}}
            )
            
            # Remove coins from teacher
            await self.users_collection.update_one(
                {"id": session.teacher_id},
                {"$inc": {"skill_coins": -session.skill_coins_paid}}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error refunding skill coins: {str(e)}")
            return False
    
    async def get_available_time_slots(self, teacher_id: str, date: datetime, skill_id: str = None) -> List[Dict[str, Any]]:
        """Get available time slots for a teacher on a specific date"""
        try:
            # Get teacher's existing sessions for the day
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            existing_sessions = await self.sessions_collection.find({
                "teacher_id": teacher_id,
                "scheduled_start": {"$gte": start_of_day, "$lte": end_of_day},
                "status": {"$in": ["scheduled", "in_progress"]}
            }).to_list(None)
            
            # For now, return basic available slots (9 AM to 5 PM in 1-hour intervals)
            # This could be enhanced with actual availability data from user preferences
            available_slots = []
            for hour in range(9, 17):  # 9 AM to 5 PM
                slot_start = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                slot_end = slot_start + timedelta(hours=1)
                
                # Check if this slot conflicts with existing sessions
                conflicts = any(
                    session["scheduled_start"] < slot_end and session["scheduled_end"] > slot_start
                    for session in existing_sessions
                )
                
                if not conflicts:
                    available_slots.append({
                        "start": slot_start,
                        "end": slot_end,
                        "duration_hours": 1
                    })
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting available time slots: {str(e)}")
            return []
    
    async def search_sessions(self, query: str, filters: Dict[str, Any], limit: int = 20) -> List[Session]:
        """Search sessions"""
        try:
            # Build search query
            search_query = {}
            
            # Text search
            if query:
                search_query["$or"] = [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"skill_name": {"$regex": query, "$options": "i"}}
                ]
            
            # Apply filters
            if filters.get("status"):
                search_query["status"] = filters["status"]
            
            if filters.get("skill_id"):
                search_query["skill_id"] = filters["skill_id"]
            
            if filters.get("teacher_id"):
                search_query["teacher_id"] = filters["teacher_id"]
            
            if filters.get("learner_id"):
                search_query["learner_id"] = filters["learner_id"]
            
            if filters.get("date_from"):
                search_query["scheduled_start"] = {"$gte": filters["date_from"]}
            
            if filters.get("date_to"):
                if "scheduled_start" in search_query:
                    search_query["scheduled_start"]["$lte"] = filters["date_to"]
                else:
                    search_query["scheduled_start"] = {"$lte": filters["date_to"]}
            
            cursor = self.sessions_collection.find(search_query).sort("scheduled_start", -1).limit(limit)
            sessions = []
            
            async for session_data in cursor:
                sessions.append(Session(**session_data))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error searching sessions: {str(e)}")
            return []