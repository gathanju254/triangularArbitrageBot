# backend/apps/users/services/profile_service.py
import logging
from typing import Dict, Any
from django.core.cache import cache
from ..models import UserProfile

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for user profile operations"""
    
    @staticmethod
    def get_user_profile(user) -> Dict[str, Any]:
        """Get user profile with cached results"""
        cache_key = f"user_profile_{user.id}"
        cached_profile = cache.get(cache_key)
        
        if cached_profile:
            return cached_profile
        
        try:
            profile = UserProfile.objects.get(user=user)
            profile_data = {
                'risk_tolerance': profile.risk_tolerance,
                'max_daily_loss': float(profile.max_daily_loss),
                'max_position_size': float(profile.max_position_size),
                'preferred_exchanges': profile.preferred_exchanges,
                'notification_preferences': profile.notification_preferences,
                'created_at': profile.created_at.isoformat(),
                'updated_at': profile.updated_at.isoformat(),
            }
            
            cache.set(cache_key, profile_data, 300)  # 5 minutes
            return profile_data
            
        except UserProfile.DoesNotExist:
            return {}
    
    @staticmethod
    def validate_risk_settings(risk_data: Dict[str, Any]) -> bool:
        """Validate risk management settings"""
        try:
            max_daily_loss = risk_data.get('max_daily_loss', 0)
            max_position_size = risk_data.get('max_position_size', 0)
            
            if max_daily_loss < 0:
                return False, "Max daily loss cannot be negative"
            
            if max_position_size < 0:
                return False, "Max position size cannot be negative"
            
            if max_daily_loss > max_position_size:
                return False, "Max daily loss cannot exceed max position size"
            
            return True, "Risk settings are valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"