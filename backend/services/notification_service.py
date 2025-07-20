from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from models import (
    Notification, NotificationCreate, NotificationResponse, NotificationUpdate,
    NotificationPreferences, NotificationType, NotificationPriority
)
import asyncio
from services.websocket_manager import WebSocketManager
import json
import uuid


class NotificationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.notifications_collection = db["notifications"]
        self.preferences_collection = db["notification_preferences"]
        self.websocket_manager = WebSocketManager()
    
    async def create_notification(self, notification_data: NotificationCreate) -> Notification:
        """Create a new notification"""
        notification = Notification(**notification_data.dict())
        
        # Store in database
        await self.notifications_collection.insert_one(notification.dict())
        
        # Send real-time notification if user is online
        await self._send_realtime_notification(notification)
        
        # Schedule email notification if needed
        await self._schedule_email_notification(notification)
        
        return notification
    
    async def create_bulk_notifications(self, notifications_data: List[NotificationCreate]) -> List[Notification]:
        """Create multiple notifications efficiently"""
        notifications = [Notification(**data.dict()) for data in notifications_data]
        
        # Bulk insert to database
        if notifications:
            await self.notifications_collection.insert_many([n.dict() for n in notifications])
        
        # Send real-time notifications
        for notification in notifications:
            await self._send_realtime_notification(notification)
        
        return notifications
    
    async def get_user_notifications(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0,
        unread_only: bool = False,
        notification_types: Optional[List[NotificationType]] = None
    ) -> List[NotificationResponse]:
        """Get notifications for a user with filtering"""
        query = {"user_id": user_id}
        
        if unread_only:
            query["is_read"] = False
            
        if notification_types:
            query["notification_type"] = {"$in": notification_types}
        
        # Get notifications sorted by creation date
        cursor = self.notifications_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        notifications = await cursor.to_list(length=limit)
        
        # Convert to response models with time_ago
        response_notifications = []
        for notif in notifications:
            response_notif = NotificationResponse(
                **notif,
                time_ago=self._get_time_ago(notif["created_at"])
            )
            response_notifications.append(response_notif)
        
        return response_notifications
    
    async def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        result = await self.notifications_collection.update_one(
            {"id": notification_id, "user_id": user_id},
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    async def mark_all_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        result = await self.notifications_collection.update_many(
            {"user_id": user_id, "is_read": False},
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count
    
    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification"""
        result = await self.notifications_collection.delete_one(
            {"id": notification_id, "user_id": user_id}
        )
        return result.deleted_count > 0
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        count = await self.notifications_collection.count_documents({
            "user_id": user_id,
            "is_read": False
        })
        return count
    
    async def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Clean up old read notifications"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        result = await self.notifications_collection.delete_many({
            "is_read": True,
            "created_at": {"$lt": cutoff_date}
        })
        return result.deleted_count
    
    # Notification Preferences Management
    async def get_user_preferences(self, user_id: str) -> NotificationPreferences:
        """Get user notification preferences"""
        preferences = await self.preferences_collection.find_one({"user_id": user_id})
        
        if not preferences:
            # Create default preferences
            default_preferences = NotificationPreferences(user_id=user_id)
            await self.preferences_collection.insert_one(default_preferences.dict())
            return default_preferences
        
        return NotificationPreferences(**preferences)
    
    async def update_user_preferences(self, user_id: str, preferences_data: Dict[str, Any]) -> NotificationPreferences:
        """Update user notification preferences"""
        preferences_data["updated_at"] = datetime.utcnow()
        
        await self.preferences_collection.update_one(
            {"user_id": user_id},
            {"$set": preferences_data},
            upsert=True
        )
        
        return await self.get_user_preferences(user_id)
    
    # Specialized notification creators
    async def notify_match_found(self, user_id: str, match_user_id: str, compatibility_score: float):
        """Send notification for new match found"""
        # Get match user info
        users_collection = self.db["users"]
        match_user = await users_collection.find_one({"id": match_user_id})
        
        if match_user:
            notification_data = NotificationCreate(
                user_id=user_id,
                notification_type=NotificationType.MATCH_FOUND,
                title="🎯 Perfect Match Found!",
                message=f"You have a {compatibility_score:.0%} compatibility with {match_user['first_name']} {match_user['last_name']}",
                priority=NotificationPriority.HIGH,
                data={
                    "match_user_id": match_user_id,
                    "compatibility_score": compatibility_score,
                    "match_skills": match_user.get("skills_offered", [])
                },
                action_url=f"/marketplace?user={match_user_id}"
            )
            await self.create_notification(notification_data)
    
    async def notify_session_reminder(self, user_id: str, session_id: str, session_title: str, starts_at: datetime):
        """Send session reminder notification"""
        time_until = starts_at - datetime.utcnow()
        time_str = "1 hour" if time_until.total_seconds() < 3600 else "1 day"
        
        notification_data = NotificationCreate(
            user_id=user_id,
            notification_type=NotificationType.SESSION_REMINDER,
            title=f"📅 Session Starting in {time_str}",
            message=f"Don't forget about your upcoming session: {session_title}",
            priority=NotificationPriority.HIGH,
            data={
                "session_id": session_id,
                "session_title": session_title,
                "starts_at": starts_at.isoformat()
            },
            action_url=f"/sessions/{session_id}",
            scheduled_for=starts_at - timedelta(hours=1)  # 1 hour before
        )
        await self.create_notification(notification_data)
    
    async def notify_achievement_earned(self, user_id: str, achievement_name: str, achievement_id: str, coins_earned: int):
        """Send achievement earned notification"""
        notification_data = NotificationCreate(
            user_id=user_id,
            notification_type=NotificationType.ACHIEVEMENT_EARNED,
            title="🏆 Achievement Unlocked!",
            message=f"Congratulations! You've earned the '{achievement_name}' achievement and {coins_earned} skill coins!",
            priority=NotificationPriority.MEDIUM,
            data={
                "achievement_id": achievement_id,
                "achievement_name": achievement_name,
                "coins_earned": coins_earned
            },
            action_url="/leaderboard?tab=achievements"
        )
        await self.create_notification(notification_data)
    
    async def notify_badge_earned(self, user_id: str, badge_name: str, badge_id: str, coins_earned: int):
        """Send badge earned notification"""
        notification_data = NotificationCreate(
            user_id=user_id,
            notification_type=NotificationType.BADGE_EARNED,
            title="🎖️ Badge Earned!",
            message=f"You've earned the '{badge_name}' badge and {coins_earned} skill coins!",
            priority=NotificationPriority.MEDIUM,
            data={
                "badge_id": badge_id,
                "badge_name": badge_name,
                "coins_earned": coins_earned
            },
            action_url="/leaderboard?tab=badges"
        )
        await self.create_notification(notification_data)
    
    async def notify_message_received(self, user_id: str, sender_name: str, conversation_id: str):
        """Send message received notification"""
        notification_data = NotificationCreate(
            user_id=user_id,
            notification_type=NotificationType.MESSAGE_RECEIVED,
            title="💬 New Message",
            message=f"You have a new message from {sender_name}",
            priority=NotificationPriority.MEDIUM,
            data={
                "conversation_id": conversation_id,
                "sender_name": sender_name
            },
            action_url=f"/messages?conversation={conversation_id}"
        )
        await self.create_notification(notification_data)
    
    async def notify_community_interaction(self, user_id: str, interaction_type: str, actor_name: str, post_title: str, post_id: str):
        """Send community interaction notification"""
        if interaction_type == "like":
            title = "👍 Post Liked"
            message = f"{actor_name} liked your post: {post_title}"
            notification_type = NotificationType.COMMUNITY_POST_LIKE
        else:  # comment
            title = "💬 New Comment"
            message = f"{actor_name} commented on your post: {post_title}"
            notification_type = NotificationType.COMMUNITY_POST_COMMENT
        
        notification_data = NotificationCreate(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=NotificationPriority.LOW,
            data={
                "post_id": post_id,
                "post_title": post_title,
                "actor_name": actor_name,
                "interaction_type": interaction_type
            },
            action_url=f"/community?post={post_id}"
        )
        await self.create_notification(notification_data)
    
    # Private helper methods
    async def _send_realtime_notification(self, notification: Notification):
        """Send real-time notification via WebSocket"""
        try:
            # Check if user is online
            if self.websocket_manager.is_user_connected(notification.user_id):
                notification_data = {
                    "type": "notification",
                    "data": {
                        "id": notification.id,
                        "notification_type": notification.notification_type,
                        "title": notification.title,
                        "message": notification.message,
                        "priority": notification.priority,
                        "data": notification.data,
                        "action_url": notification.action_url,
                        "created_at": notification.created_at.isoformat(),
                        "time_ago": self._get_time_ago(notification.created_at)
                    }
                }
                
                await self.websocket_manager.send_message_to_user(
                    notification.user_id, 
                    json.dumps(notification_data)
                )
        except Exception as e:
            print(f"Error sending real-time notification: {e}")
    
    async def _schedule_email_notification(self, notification: Notification):
        """Schedule email notification (placeholder for email service integration)"""
        # Check user preferences
        preferences = await self.get_user_preferences(notification.user_id)
        
        if not preferences.email_notifications:
            return
            
        # Check if this notification type is enabled
        if notification.notification_type == NotificationType.MATCH_FOUND and not preferences.match_notifications:
            return
        elif notification.notification_type == NotificationType.SESSION_REMINDER and not preferences.session_reminders:
            return
        # ... add other type checks
        
        # TODO: Integrate with email service (SendGrid, SES, etc.)
        # For now, just log the email that would be sent
        print(f"EMAIL SCHEDULED: {notification.title} to user {notification.user_id}")
    
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
    
    async def get_notification_stats(self, user_id: str) -> Dict[str, Any]:
        """Get notification statistics for a user"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$notification_type",
                "count": {"$sum": 1},
                "unread_count": {"$sum": {"$cond": [{"$eq": ["$is_read", False]}, 1, 0]}}
            }}
        ]
        
        stats = await self.notifications_collection.aggregate(pipeline).to_list(length=None)
        
        total_notifications = sum(stat["count"] for stat in stats)
        total_unread = sum(stat["unread_count"] for stat in stats)
        
        return {
            "total_notifications": total_notifications,
            "total_unread": total_unread,
            "by_type": {stat["_id"]: {"count": stat["count"], "unread": stat["unread_count"]} for stat in stats}
        }