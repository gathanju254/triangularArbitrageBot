# backend/apps/users/services/settings_service.py
import logging
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.utils import timezone

from ..models.settings import UserSettings, BotConfiguration

logger = logging.getLogger(__name__)

class SettingsService:
    """Professional settings management service"""
    
    @staticmethod
    def get_user_settings(user) -> UserSettings:
        """Get or create user settings with cache"""
        cache_key = f"user_settings_{user.id}"
        cached_settings = cache.get(cache_key)
        
        if cached_settings:
            return cached_settings
        
        settings, created = UserSettings.objects.get_or_create(user=user)
        
        # Cache for 5 minutes
        cache.set(cache_key, settings, 300)
        
        if created:
            logger.info(f"Created new settings for user: {user.username}")
        
        return settings
    
    @staticmethod
    def update_user_settings(user, settings_data: Dict[str, Any]) -> UserSettings:
        """Update user settings with validation and cache invalidation"""
        settings = SettingsService.get_user_settings(user)
        
        # Separate fields by category for validation
        trading_fields = [
            'trading_mode', 'max_concurrent_trades', 'min_trade_amount', 
            'slippage_tolerance'
        ]
        
        risk_fields = [
            'risk_tolerance', 'max_daily_loss', 'max_position_size', 
            'max_drawdown', 'stop_loss_enabled', 'take_profit_enabled',
            'stop_loss_percent', 'take_profit_percent'
        ]
        
        notification_fields = [
            'email_notifications', 'push_notifications', 
            'trading_alerts', 'risk_alerts'
        ]
        
        exchange_fields = [
            'preferred_exchanges', 'min_profit_threshold'
        ]
        
        # Update fields
        for field, value in settings_data.items():
            if hasattr(settings, field):
                setattr(settings, field, value)
        
        # Set audit field
        settings.last_modified_by = user
        
        # Validate and save
        settings.full_clean()
        settings.save()
        
        # Clear cache
        cache.delete(f"user_settings_{user.id}")
        
        logger.info(f"Updated settings for user: {user.username}")
        return settings
    
    @staticmethod
    def get_trading_settings(user) -> Dict[str, Any]:
        """Get trading-specific settings"""
        settings = SettingsService.get_user_settings(user)
        
        return {
            'trading_mode': settings.trading_mode,
            'max_concurrent_trades': settings.max_concurrent_trades,
            'min_trade_amount': float(settings.min_trade_amount),
            'slippage_tolerance': float(settings.slippage_tolerance),
            'auto_trading': settings.trading_mode != 'manual'
        }
    
    @staticmethod
    def get_risk_settings(user) -> Dict[str, Any]:
        """Get risk management settings"""
        settings = SettingsService.get_user_settings(user)
        
        return {
            'risk_tolerance': settings.risk_tolerance,
            'max_daily_loss': float(settings.max_daily_loss),
            'max_position_size': float(settings.max_position_size),
            'max_drawdown': float(settings.max_drawdown),
            'stop_loss_enabled': settings.stop_loss_enabled,
            'take_profit_enabled': settings.take_profit_enabled,
            'stop_loss_percent': float(settings.stop_loss_percent),
            'take_profit_percent': float(settings.take_profit_percent)
        }
    
    @staticmethod
    def get_notification_settings(user) -> Dict[str, Any]:
        """Get notification settings"""
        settings = SettingsService.get_user_settings(user)
        
        return {
            'email_notifications': settings.email_notifications,
            'push_notifications': settings.push_notifications,
            'trading_alerts': settings.trading_alerts,
            'risk_alerts': settings.risk_alerts
        }
    
    @staticmethod
    def get_exchange_settings(user) -> Dict[str, Any]:
        """Get exchange settings"""
        settings = SettingsService.get_user_settings(user)
        bot_config = BotConfiguration.get_config()
        
        return {
            'preferred_exchanges': settings.preferred_exchanges,
            'min_profit_threshold': float(settings.min_profit_threshold),
            'enabled_exchanges': bot_config.enabled_exchanges
        }
    
    @staticmethod
    def get_bot_configuration() -> BotConfiguration:
        """Get system-wide bot configuration"""
        return BotConfiguration.get_config()
    
    @staticmethod
    def update_bot_configuration(config_data: Dict[str, Any]) -> BotConfiguration:
        """Update system-wide bot configuration"""
        config = BotConfiguration.get_config()
        
        for field, value in config_data.items():
            if hasattr(config, field):
                setattr(config, field, value)
        
        config.save()
        
        logger.info("Updated bot configuration")
        return config
    
    @staticmethod
    def export_user_settings(user) -> Dict[str, Any]:
        """Export all user settings for backup"""
        settings = SettingsService.get_user_settings(user)
        
        return {
            'exported_at': timezone.now().isoformat(),
            'user_id': user.id,
            'username': user.username,
            'trading_settings': SettingsService.get_trading_settings(user),
            'risk_settings': SettingsService.get_risk_settings(user),
            'notification_settings': SettingsService.get_notification_settings(user),
            'exchange_settings': SettingsService.get_exchange_settings(user)
        }
    
    @staticmethod
    def reset_to_defaults(user) -> UserSettings:
        """Reset user settings to defaults"""
        defaults = {
            'trading_mode': 'manual',
            'max_concurrent_trades': 3,
            'min_trade_amount': 10.00,
            'slippage_tolerance': 0.1,
            'risk_tolerance': 'medium',
            'max_daily_loss': 1000.00,
            'max_position_size': 5000.00,
            'max_drawdown': 20.0,
            'stop_loss_enabled': True,
            'take_profit_enabled': True,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 5.0,
            'email_notifications': True,
            'push_notifications': False,
            'trading_alerts': True,
            'risk_alerts': True,
            'preferred_exchanges': ['binance', 'kraken'],
            'min_profit_threshold': 0.3
        }
        
        return SettingsService.update_user_settings(user, defaults)