# backend/apps/users/validators.py

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re

def validate_phone_number(value):
    """
    Validate phone number format (international format)
    """
    # Basic phone number validation - adjust regex based on your needs
    phone_regex = r'^\+?1?\d{9,15}$'
    if not re.match(phone_regex, value):
        raise ValidationError(
            _('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
        )

def validate_password_strength(value):
    """
    Validate password strength
    """
    if len(value) < 8:
        raise ValidationError(
            _('Password must be at least 8 characters long.')
        )
    
    if not any(char.isdigit() for char in value):
        raise ValidationError(
            _('Password must contain at least one digit.')
        )
    
    if not any(char.isalpha() for char in value):
        raise ValidationError(
            _('Password must contain at least one letter.')
        )

def validate_username(value):
    """
    Validate username format
    """
    if len(value) < 3:
        raise ValidationError(
            _('Username must be at least 3 characters long.')
        )
    
    if not re.match(r'^[a-zA-Z0-9_]+$', value):
        raise ValidationError(
            _('Username can only contain letters, numbers, and underscores.')
        )

def validate_email_domain(value):
    """
    Validate email domain (basic check)
    """
    from django.core.validators import validate_email
    
    # First validate basic email format
    validate_email(value)
    
    # Additional domain validation if needed
    domain = value.split('@')[-1]
    if domain in ['example.com', 'test.com']:  # Add domains you want to block
        raise ValidationError(
            _('This email domain is not allowed.')
        )

def validate_trading_amount(value):
    """
    Validate trading amount (must be positive)
    """
    if value <= 0:
        raise ValidationError(
            _('Trading amount must be greater than zero.')
        )

def validate_api_key_format(value, exchange):
    """
    Validate API key format for different exchanges
    """
    if not value or len(value.strip()) == 0:
        raise ValidationError(
            _('API key cannot be empty.')
        )
    
    # Basic length validation for common exchanges
    min_lengths = {
        'binance': 64,
        'kraken': 56,
        'coinbase': 64,
        'huobi': 24,
        'okx': 46
    }
    
    if exchange.lower() in min_lengths:
        min_len = min_lengths[exchange.lower()]
        if len(value) < min_len:
            raise ValidationError(
                _(f'API key for {exchange} seems too short. Expected at least {min_len} characters.')
            )

def validate_percentage(value):
    """
    Validate percentage values (0-100)
    """
    if value < 0 or value > 100:
        raise ValidationError(
            _('Percentage must be between 0 and 100.')
        )

def validate_positive_number(value):
    """
    Validate that a number is positive
    """
    if value < 0:
        raise ValidationError(
            _('Value must be positive.')
        )

def validate_json_format(value):
    """
    Validate JSON string format
    """
    import json
    try:
        if isinstance(value, str):
            json.loads(value)
    except json.JSONDecodeError:
        raise ValidationError(
            _('Invalid JSON format.')
        )

class TradingValidator:
    """
    Validator class for trading-related validations
    """
    
    @staticmethod
    def validate_trade_size(size, min_trade=1.0, max_trade=10000.0):
        """
        Validate trade size within acceptable range
        """
        if size < min_trade:
            raise ValidationError(
                _(f'Trade size must be at least ${min_trade:.2f}.')
            )
        
        if size > max_trade:
            raise ValidationError(
                _(f'Trade size cannot exceed ${max_trade:.2f}.')
            )
    
    @staticmethod
    def validate_profit_threshold(threshold):
        """
        Validate profit threshold (typically 0.1% to 10%)
        """
        if threshold < 0.1:
            raise ValidationError(
                _('Profit threshold must be at least 0.1%.')
            )
        
        if threshold > 10.0:
            raise ValidationError(
                _('Profit threshold cannot exceed 10%.')
            )
    
    @staticmethod
    def validate_risk_limits(max_daily_loss, max_position_size, base_balance):
        """
        Validate risk management limits
        """
        if max_daily_loss <= 0:
            raise ValidationError(
                _('Maximum daily loss must be positive.')
            )
        
        if max_position_size <= 0:
            raise ValidationError(
                _('Maximum position size must be positive.')
            )
        
        if max_position_size > base_balance * 0.5:  # Max 50% of base balance
            raise ValidationError(
                _('Maximum position size cannot exceed 50% of base balance.')
            )
        
        if max_daily_loss > base_balance * 0.1:  # Max 10% of base balance
            raise ValidationError(
                _('Maximum daily loss cannot exceed 10% of base balance.')
            )

class UserSettingsValidator:
    """
    Validator class for user settings
    """
    
    @staticmethod
    def validate_notification_settings(settings):
        """
        Validate notification settings
        """
        allowed_keys = ['email_notifications', 'push_notifications', 'trading_alerts', 'risk_alerts']
        
        for key in settings.keys():
            if key not in allowed_keys:
                raise ValidationError(
                    _(f'Invalid notification setting: {key}')
                )
    
    @staticmethod
    def validate_trading_preferences(preferences):
        """
        Validate trading preferences
        """
        allowed_risk_levels = ['low', 'medium', 'high']
        
        if 'risk_tolerance' in preferences:
            if preferences['risk_tolerance'] not in allowed_risk_levels:
                raise ValidationError(
                    _(f'Risk tolerance must be one of: {", ".join(allowed_risk_levels)}')
                )
        
        if 'preferred_exchanges' in preferences:
            if not isinstance(preferences['preferred_exchanges'], list):
                raise ValidationError(
                    _('Preferred exchanges must be a list.')
                )

# Export commonly used validators
__all__ = [
    'validate_phone_number',
    'validate_password_strength',
    'validate_username',
    'validate_email_domain',
    'validate_trading_amount',
    'validate_api_key_format',
    'validate_percentage',
    'validate_positive_number',
    'validate_json_format',
    'TradingValidator',
    'UserSettingsValidator'
]