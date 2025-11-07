# backend/apps/users/services/notification_service.py
import logging
from typing import Dict, Any, List
from django.utils import timezone
from ..models import UserProfile

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for user notification management"""
    
    @staticmethod
    def get_user_notification_preferences(user) -> Dict[str, Any]:
        """Get user notification preferences"""
        try:
            profile = UserProfile.objects.get(user=user)
            return profile.notification_preferences or {
                'email': True,
                'push': True,
                'trading_alerts': True,
                'security_alerts': True,
                'price_alerts': False,
            }
        except UserProfile.DoesNotExist:
            return {
                'email': True,
                'push': True,
                'trading_alerts': True,
                'security_alerts': True,
                'price_alerts': False,
            }
    
    @staticmethod
    def update_notification_preferences(user, preferences: Dict[str, Any]) -> bool:
        """Update user notification preferences"""
        try:
            profile = UserProfile.objects.get(user=user)
            current_prefs = profile.notification_preferences or {}
            current_prefs.update(preferences)
            profile.notification_preferences = current_prefs
            profile.save()
            return True
        except Exception as e:
            logger.error(f"Failed to update notification preferences: {e}")
            return False
    
    @staticmethod
    def should_send_notification(user, notification_type: str) -> bool:
        """Check if user should receive a specific notification type"""
        prefs = NotificationService.get_user_notification_preferences(user)
        return prefs.get(notification_type, False)