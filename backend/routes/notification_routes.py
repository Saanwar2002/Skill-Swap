from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from auth import AuthService
from models import (
    User, NotificationCreate, NotificationResponse, NotificationUpdate,
    NotificationPreferences, NotificationType, NotificationPriority
)
from services.notification_service import NotificationService

security = HTTPBearer()

def create_notification_router(db: AsyncIOMotorDatabase) -> APIRouter:
    router = APIRouter()
    auth_service = AuthService(db)
    
    async def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current user from token"""
        return await auth_service.get_current_user(credentials.credentials)
    
    @router.get("/", response_model=List[NotificationResponse])
    async def get_notifications(
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        unread_only: bool = Query(False),
        notification_types: Optional[str] = Query(None, description="Comma-separated notification types"),
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Get user notifications with filtering options"""
        notification_service = NotificationService(db)
        
        # Parse notification types if provided
        types_filter = None
        if notification_types:
            try:
                types_filter = [NotificationType(t.strip()) for t in notification_types.split(",")]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid notification type")
        
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            unread_only=unread_only,
            notification_types=types_filter
        )
        
        return notifications

    @router.get("/count")
    async def get_unread_count(
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Get count of unread notifications"""
        notification_service = NotificationService(db)
        count = await notification_service.get_unread_count(current_user.id)
        return {"unread_count": count}

    @router.get("/stats")
    async def get_notification_stats(
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Get notification statistics"""
        notification_service = NotificationService(db)
        stats = await notification_service.get_notification_stats(current_user.id)
        return stats

    @router.put("/{notification_id}")
    async def update_notification(
        notification_id: str,
        update_data: NotificationUpdate,
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Update notification (mark as read, dismiss, etc.)"""
        notification_service = NotificationService(db)
        
        if update_data.is_read is not None:
            success = await notification_service.mark_notification_read(notification_id, current_user.id)
            if not success:
                raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "message": "Notification updated successfully"}

    @router.put("/mark-all-read")
    async def mark_all_read(
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Mark all notifications as read"""
        notification_service = NotificationService(db)
        count = await notification_service.mark_all_read(current_user.id)
        return {"success": True, "marked_read": count}

    @router.delete("/{notification_id}")
    async def delete_notification(
        notification_id: str,
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Delete a notification"""
        notification_service = NotificationService(db)
        success = await notification_service.delete_notification(notification_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "message": "Notification deleted successfully"}

    @router.post("/", response_model=dict)
    async def create_notification(
        notification_data: NotificationCreate,
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Create a notification (admin/system use)"""
        # Only allow creating notifications for the current user or if they're admin
        if notification_data.user_id != current_user.id:
            # TODO: Add admin role check here
            raise HTTPException(status_code=403, detail="Cannot create notifications for other users")
        
        notification_service = NotificationService(db)
        notification = await notification_service.create_notification(notification_data)
        
        return {
            "success": True, 
            "message": "Notification created successfully",
            "notification_id": notification.id
        }

    # Notification Preferences
    @router.get("/preferences", response_model=NotificationPreferences)
    async def get_notification_preferences(
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Get user notification preferences"""
        notification_service = NotificationService(db)
        preferences = await notification_service.get_user_preferences(current_user.id)
        return preferences

    @router.put("/preferences", response_model=NotificationPreferences)
    async def update_notification_preferences(
        preferences_update: Dict[str, Any],
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Update user notification preferences"""
        notification_service = NotificationService(db)
        preferences = await notification_service.update_user_preferences(
            current_user.id, 
            preferences_update
        )
        return preferences

    # Quick notification actions (for other services to use)
    @router.post("/quick/match-found")
    async def notify_match_found(
        data: Dict[str, Any],
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Quick notification for match found"""
        notification_service = NotificationService(db)
        
        await notification_service.notify_match_found(
            user_id=current_user.id,
            match_user_id=data["match_user_id"],
            compatibility_score=data["compatibility_score"]
        )
        
        return {"success": True, "message": "Match notification sent"}

    @router.post("/quick/session-reminder")
    async def notify_session_reminder(
        data: Dict[str, Any],
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Quick notification for session reminder"""
        notification_service = NotificationService(db)
        
        await notification_service.notify_session_reminder(
            user_id=current_user.id,
            session_id=data["session_id"],
            session_title=data["session_title"],
            starts_at=datetime.fromisoformat(data["starts_at"])
        )
        
        return {"success": True, "message": "Session reminder sent"}

    @router.post("/quick/achievement-earned")
    async def notify_achievement_earned(
        data: Dict[str, Any],
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Quick notification for achievement earned"""
        notification_service = NotificationService(db)
        
        await notification_service.notify_achievement_earned(
            user_id=current_user.id,
            achievement_name=data["achievement_name"],
            achievement_id=data["achievement_id"],
            coins_earned=data.get("coins_earned", 0)
        )
        
        return {"success": True, "message": "Achievement notification sent"}

    @router.post("/quick/message-received")
    async def notify_message_received(
        data: Dict[str, Any],
        current_user: User = Depends(get_current_user_dependency)
    ):
        """Quick notification for message received"""
        notification_service = NotificationService(db)
        
        await notification_service.notify_message_received(
            user_id=current_user.id,
            sender_name=data["sender_name"],
            conversation_id=data["conversation_id"]
        )
        
        return {"success": True, "message": "Message notification sent"}
    
    return router