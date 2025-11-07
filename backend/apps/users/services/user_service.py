# backend/apps/users/services/user_service.py
import logging
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from ..models import User, UserProfile

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations"""
    
    CACHE_TIMEOUT = 600
    CACHE_PREFIX = "user_service"
    
    @staticmethod
    def _get_cache_key(key_suffix: str) -> str:
        return f"{UserService.CACHE_PREFIX}:{key_suffix}"
    
    @staticmethod
    @transaction.atomic
    def create_user(
        username: str,
        email: str,
        password: str,
        user_type: str = 'trader',
        phone: str = None,
        timezone: str = 'UTC',
        **extra_fields
    ) -> User:
        """Create a new user with profile"""
        logger.info(f"👤 Creating user: {username}")
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            raise ValueError(f"Username {username} already exists")
        
        if User.objects.filter(email=email).exists():
            raise ValueError(f"Email {email} already exists")
        
        try:
            # Create user
            user = User(
                username=username,
                email=email,
                password=make_password(password),
                user_type=user_type,
                phone=phone,
                timezone=timezone,
                **extra_fields
            )
            
            user.full_clean()
            user.save()
            
            # Create user profile
            profile = UserProfile(user=user)
            profile.full_clean()
            profile.save()
            
            logger.info(f"✅ User created successfully: {username} (ID: {user.id})")
            return user
            
        except Exception as e:
            logger.error(f"❌ Failed to create user {username}: {e}")
            raise ValueError(f"Failed to create user: {str(e)}") from e
    
    @staticmethod
    def update_user_profile(user: User, profile_data: Dict[str, Any]) -> UserProfile:
        """Update user profile with validation"""
        logger.info(f"🔄 Updating profile for user: {user.username}")
        
        try:
            profile = UserProfile.objects.get(user=user)
            
            # Update allowed fields
            allowed_fields = ['risk_tolerance', 'max_daily_loss', 'max_position_size', 
                            'preferred_exchanges', 'notification_preferences']
            
            for field in allowed_fields:
                if field in profile_data:
                    setattr(profile, field, profile_data[field])
            
            # Validate and save
            profile.full_clean()
            profile.save()
            
            # Clear cache
            cache_key = UserService._get_cache_key(f"profile_{user.id}")
            cache.delete(cache_key)
            
            logger.info(f"✅ Profile updated for user: {user.username}")
            return profile
            
        except UserProfile.DoesNotExist:
            logger.error(f"❌ Profile not found for user: {user.username}")
            raise ValueError("User profile not found")
        except Exception as e:
            logger.error(f"❌ Failed to update profile: {e}")
            raise ValueError(f"Failed to update profile: {str(e)}") from e
    
    @staticmethod
    def get_user_stats(user: User) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        cache_key = UserService._get_cache_key(f"stats_{user.id}")
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        try:
            from .api_key_service import APIKeyService
            
            api_key_stats = APIKeyService.get_user_api_key_stats(user)
            
            stats = {
                'user_info': {
                    'username': user.username,
                    'email': user.email,
                    'user_type': user.user_type,
                    'is_verified': user.is_verified,
                    'date_joined': user.date_joined.isoformat(),
                },
                'api_keys': api_key_stats,
                'trading_stats': {
                    'total_trades': 0,  # Would come from trading app
                    'successful_trades': 0,
                    'total_volume': 0,
                }
            }
            
            cache.set(cache_key, stats, UserService.CACHE_TIMEOUT)
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {
                'user_info': {
                    'username': user.username,
                    'email': user.email,
                    'user_type': user.user_type,
                    'is_verified': user.is_verified,
                    'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                },
                'api_keys': {},
                'trading_stats': {}
            }
    
    @staticmethod
    def deactivate_user(user: User, reason: str = None) -> bool:
        """Deactivate user account"""
        logger.warning(f"🚫 Deactivating user: {user.username}")
        
        try:
            # Deactivate all API keys
            from ..models import APIKey
            APIKey.objects.filter(user=user).update(is_active=False)
            
            # Deactivate user (you might want to use is_active field instead)
            user.is_active = False
            user.save()
            
            # Clear all user-related caches
            cache_keys = [
                UserService._get_cache_key(f"stats_{user.id}"),
                UserService._get_cache_key(f"profile_{user.id}"),
            ]
            cache.delete_many(cache_keys)
            
            logger.info(f"✅ User deactivated: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to deactivate user: {e}")
            return False