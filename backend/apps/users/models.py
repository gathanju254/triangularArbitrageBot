# backend/apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.users.utils.security import (
    encrypt_data,
    decrypt_data,
    safe_encrypt_data,
    safe_decrypt_data,
)
import logging

logger = logging.getLogger(__name__)

class User(AbstractUser):
    USER_TYPES = [
        ('admin', 'Administrator'),
        ('trader', 'Trader'),
        ('viewer', 'Viewer'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='trader')
    phone = models.CharField(max_length=20, blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.user_type})"

class UserProfile(models.Model):
    RISK_TOLERANCE_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'), 
        ('high', 'High'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    risk_tolerance = models.CharField(
        max_length=20,
        choices=RISK_TOLERANCE_CHOICES,
        default='medium'
    )
    max_daily_loss = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    max_position_size = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00)
    preferred_exchanges = models.JSONField(default=list)
    notification_preferences = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile for {self.user.username}"

    def clean(self):
        """Validate profile data"""
        if self.max_daily_loss < 0:
            raise ValidationError({'max_daily_loss': 'Max daily loss cannot be negative'})
        if self.max_position_size < 0:
            raise ValidationError({'max_position_size': 'Max position size cannot be negative'})

class APIKey(models.Model):
    EXCHANGE_CHOICES = [
        ('binance', 'Binance'),
        ('coinbase', 'Coinbase'),
        ('kraken', 'Kraken'),
        ('kucoin', 'KuCoin'),
        ('okx', 'OKX'),
        ('huobi', 'Huobi'),
        ('bybit', 'Bybit'),
    ]
    
    PERMISSION_SCOPES = [
        ('read', 'Read Only'),
        ('trade', 'Trading'),
        ('withdraw', 'Withdrawal'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    exchange = models.CharField(max_length=50, choices=EXCHANGE_CHOICES)
    label = models.CharField(max_length=100, blank=True, null=True, 
                           help_text="A friendly name to identify this API key")
    api_key = models.TextField(help_text="The API key from the exchange")
    secret_key = models.TextField(help_text="The secret key from the exchange")
    passphrase = models.TextField(blank=True, null=True, 
                                help_text="Passphrase (required for some exchanges like OKX, Coinbase, KuCoin)")
    
    # Security & Permissions
    is_encrypted = models.BooleanField(default=False, 
                                     help_text="Whether the keys are encrypted in the database")
    is_active = models.BooleanField(default=True, 
                                  help_text="Whether this API key is active for trading")
    is_validated = models.BooleanField(default=False, 
                                     help_text="Whether the API key has been validated with the exchange")
    permissions = models.JSONField(
        default=list,
        help_text="List of allowed permissions: ['read', 'trade']"
    )
    
    # Rate limiting
    requests_per_minute = models.IntegerField(default=60, help_text="Maximum requests per minute")
    last_request_time = models.DateTimeField(null=True, blank=True, help_text="Last API request time")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True,
                                   help_text="Last time this API key was used")
    last_validated = models.DateTimeField(null=True, blank=True,
                                        help_text="Last time this API key was validated")

    class Meta:
        db_table = 'api_keys'
        unique_together = (('user', 'exchange'),)
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['-created_at']

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.user.username} - {self.exchange} - {self.label or 'No Label'} ({status})"

    def clean(self):
        """Validate API key data before saving"""
        # Check if exchange requires passphrase
        if self.exchange.lower() in ['okx', 'coinbase', 'kucoin'] and not self.passphrase:
            raise ValidationError({
                'passphrase': f'{self.exchange} requires a passphrase for API authentication'
            })
        
        # Validate API key format (basic checks)
        if self.api_key and len(self.api_key.strip()) < 20:
            raise ValidationError({
                'api_key': 'API key appears to be too short'
            })
        
        if self.secret_key and len(self.secret_key.strip()) < 20:
            raise ValidationError({
                'secret_key': 'Secret key appears to be too short'
            })
        
        # Validate permissions
        if self.permissions and not all(perm in [p[0] for p in self.PERMISSION_SCOPES] for perm in self.permissions):
            raise ValidationError({
                'permissions': f'Invalid permissions. Must be one of: {[p[0] for p in self.PERMISSION_SCOPES]}'
            })

    def _is_already_encrypted(self, value: str) -> bool:
        """
        Check if a value is already encrypted.
        Uses multiple strategies to detect encrypted data.
        """
        if not value:
            return False
        
        # Strategy 1: Check for legacy 'encrypted:' prefix
        if value.startswith('encrypted:'):
            return True
        
        # Strategy 2: Check if it looks like a Fernet token
        # Fernet tokens are URL-safe base64, typically 100+ characters
        if len(value) >= 100 and all(c in 
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=' 
            for c in value):
            try:
                # Try to decode as base64
                import base64
                base64.urlsafe_b64decode(value)
                return True
            except Exception:
                pass
        
        return False

    def _encrypt_field(self, field_name: str, use_legacy_prefix: bool = False) -> bool:
        """
        Helper method to encrypt a field.
        
        Args:
            field_name: Name of the field to encrypt
            use_legacy_prefix: Whether to use the legacy 'encrypted:' prefix
        """
        value = getattr(self, field_name)
        
        if not value:
            return True  # No value to encrypt
            
        if self._is_already_encrypted(value):
            logger.debug(f"Field {field_name} is already encrypted")
            return True

        try:
            # Use safe encryption with fallback for development
            encrypted_value = safe_encrypt_data(value, fallback_to_plaintext=True)
            
            if use_legacy_prefix:
                encrypted_value = f"encrypted:{encrypted_value}"
                
            setattr(self, field_name, encrypted_value)
            logger.debug(f"✅ Successfully encrypted field {field_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to encrypt {field_name}: {e}")
            # In development, we might allow plaintext storage as fallback
            from django.conf import settings
            if settings.DEBUG:
                logger.warning(f"Storing {field_name} as plaintext in DEBUG mode")
                return True
            return False

    def _decrypt_field(self, field_name: str, handle_legacy_prefix: bool = True) -> bool:
        """
        Helper method to decrypt a field.
        
        Args:
            field_name: Name of the field to decrypt
            handle_legacy_prefix: Whether to handle legacy 'encrypted:' prefix
        """
        value = getattr(self, field_name)
        
        if not value:
            return True  # No value to decrypt

        # Handle legacy prefix if present
        if handle_legacy_prefix and value.startswith('encrypted:'):
            value = value[len('encrypted:'):]
            
        if not self._is_already_encrypted(value):
            logger.debug(f"Field {field_name} is not encrypted, skipping decryption")
            return True

        try:
            # Use safe decryption with fallback
            decrypted_value = safe_decrypt_data(value, fallback_to_token=True)
            setattr(self, field_name, decrypted_value)
            logger.debug(f"✅ Successfully decrypted field {field_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to decrypt {field_name}: {e}")
            # In development, keep the encrypted value
            from django.conf import settings
            if settings.DEBUG:
                logger.warning(f"Keeping {field_name} encrypted in DEBUG mode due to decryption failure")
                return False
            raise ValueError(f"Failed to decrypt {field_name}") from e

    def encrypt_keys(self, use_legacy_prefix: bool = False) -> None:
        """
        Encrypt all sensitive fields.
        
        Args:
            use_legacy_prefix: Whether to use legacy 'encrypted:' prefix for backward compatibility
        """
        if not self.is_encrypted:
            logger.info(f"🔐 Encrypting keys for {self.exchange} (user: {self.user.username})...")
            
            # Track encryption success
            encryption_results = [
                self._encrypt_field('api_key', use_legacy_prefix),
                self._encrypt_field('secret_key', use_legacy_prefix),
                self._encrypt_field('passphrase', use_legacy_prefix) if self.passphrase else True
            ]
            
            if all(encryption_results):
                self.is_encrypted = True
                logger.info("✅ All keys encrypted successfully")
            else:
                failed_fields = [field for field, success in 
                               zip(['api_key', 'secret_key', 'passphrase'], encryption_results) 
                               if not success]
                error_msg = f"Failed to encrypt fields: {', '.join(failed_fields)}"
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)

    def decrypt_keys(self, handle_legacy_prefix: bool = True) -> None:
        """
        Decrypt all sensitive fields for use (in-memory only).
        
        Args:
            handle_legacy_prefix: Whether to handle legacy 'encrypted:' prefix
        """
        if self.is_encrypted:
            logger.info(f"🔓 Decrypting keys for {self.exchange} (user: {self.user.username})...")
            
            decryption_results = [
                self._decrypt_field('api_key', handle_legacy_prefix),
                self._decrypt_field('secret_key', handle_legacy_prefix),
                self._decrypt_field('passphrase', handle_legacy_prefix) if self.passphrase else True
            ]
            
            if all(decryption_results):
                logger.info("✅ All keys decrypted successfully")
            else:
                failed_fields = [field for field, success in 
                               zip(['api_key', 'secret_key', 'passphrase'], decryption_results) 
                               if not success]
                error_msg = f"Failed to decrypt fields: {', '.join(failed_fields)}"
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)

    def get_decrypted_keys(self, handle_legacy_prefix: bool = True) -> dict:
        """
        Get decrypted keys without modifying the instance.
        Returns a dictionary with decrypted values.
        
        Args:
            handle_legacy_prefix: Whether to handle legacy 'encrypted:' prefix
        """
        logger.debug(f"🔓 Getting decrypted keys for {self.exchange}")
        
        if not self.is_encrypted:
            logger.debug("Keys are not encrypted, returning as-is")
            return {
                'api_key': self.api_key,
                'secret_key': self.secret_key,
                'passphrase': self.passphrase
            }
        
        try:
            decrypted_data = {}
            
            # Decrypt each field individually
            for field_name in ['api_key', 'secret_key', 'passphrase']:
                value = getattr(self, field_name)
                
                if not value:
                    decrypted_data[field_name] = None
                    continue
                    
                # Handle legacy prefix
                if handle_legacy_prefix and value.startswith('encrypted:'):
                    value = value[len('encrypted:'):]
                
                try:
                    decrypted_data[field_name] = safe_decrypt_data(value, fallback_to_token=False)
                except Exception as e:
                    logger.error(f"Failed to decrypt {field_name}: {e}")
                    raise ValueError(f"Failed to decrypt {field_name}") from e
            
            logger.debug("✅ Successfully retrieved decrypted keys")
            return decrypted_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get decrypted keys: {e}")
            raise ValueError("Failed to decrypt API key data") from e

    def mark_as_used(self) -> None:
        """Mark the API key as used (update last_used timestamp)"""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])
        logger.debug(f"📝 Marked API key {self.id} as used")

    def mark_as_validated(self, is_valid: bool = True) -> None:
        """Mark the API key as validated or invalidated"""
        self.is_validated = is_valid
        self.last_validated = timezone.now()
        self.save(update_fields=['is_validated', 'last_validated'])
        logger.info(f"✅ Marked API key {self.id} as {'validated' if is_valid else 'invalidated'}")

    def validate_format(self) -> bool:
        """Validate the format of API key data"""
        try:
            self.clean()  # This will raise ValidationError if invalid
            return True
        except ValidationError:
            return False

    def check_rate_limit(self) -> bool:
        """Check if API key is within rate limits"""
        if not self.last_request_time:
            return True
            
        time_since_last_request = timezone.now() - self.last_request_time
        requests_per_second = self.requests_per_minute / 60.0
        min_time_between_requests = 1.0 / requests_per_second
        
        return time_since_last_request.total_seconds() >= min_time_between_requests

    def record_usage(self) -> None:
        """Record API key usage for rate limiting"""
        self.last_request_time = timezone.now()
        self.save(update_fields=['last_request_time'])

    def has_permission(self, permission: str) -> bool:
        """Check if API key has specific permission"""
        return permission in self.permissions

    def save(self, *args, **kwargs):
        """Ensure encryption on save with comprehensive logging"""
        logger.info(f"💾 Saving API key for {self.exchange} (user: {self.user.username})")
        
        # Log pre-save state (safely, without exposing sensitive data)
        logger.debug(f"📦 Pre-save - Encrypted: {self.is_encrypted}, Active: {self.is_active}")
        logger.debug(f"📦 Pre-save - Has API key: {bool(self.api_key)}, Has secret: {bool(self.secret_key)}")
        
        # Validate the instance before saving
        try:
            self.full_clean()
        except ValidationError as e:
            logger.error(f"❌ Validation failed before save: {e}")
            raise

        # Encrypt before saving if not already encrypted and we have data to encrypt
        if not self.is_encrypted and (self.api_key or self.secret_key):
            try:
                # For backward compatibility, use legacy prefix for existing code
                use_legacy_prefix = hasattr(self, '_use_legacy_prefix') and self._use_legacy_prefix
                self.encrypt_keys(use_legacy_prefix=use_legacy_prefix)
            except Exception as e:
                logger.error(f"❌ Encryption failed during save: {e}")
                # Don't save if encryption fails (unless in DEBUG mode)
                from django.conf import settings
                if not settings.DEBUG:
                    raise
        
        # Update timestamp
        self.updated_at = timezone.now()
        
        # Perform the save
        super().save(*args, **kwargs)
        
        # Log post-save state
        logger.debug(f"📦 Post-save - Encrypted: {self.is_encrypted}")
        logger.info("✅ API key saved successfully")

    @classmethod
    def get_active_keys_for_user(cls, user):
        """Get all active API keys for a user"""
        return cls.objects.filter(user=user, is_active=True)

    @classmethod
    def get_validated_keys_for_user(cls, user):
        """Get all active and validated API keys for a user"""
        return cls.objects.filter(user=user, is_active=True, is_validated=True)

    @classmethod
    def get_trading_keys_for_user(cls, user):
        """Get API keys with trading permissions"""
        return cls.objects.filter(
            user=user, 
            is_active=True, 
            is_validated=True
        ).filter(permissions__contains=['trade'])

    @property
    def requires_passphrase(self) -> bool:
        """Check if this exchange requires a passphrase"""
        return self.exchange.lower() in ['okx', 'coinbase', 'kucoin']

    @property
    def is_usable(self) -> bool:
        """Check if this API key is usable (active and validated)"""
        return self.is_active and self.is_validated

    @property
    def display_name(self) -> str:
        """Get a display name for the API key"""
        if self.label:
            return f"{self.exchange} - {self.label}"
        return self.exchange


class APIKeyUsageLog(models.Model):
    """Track API key usage for security and analytics"""
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='usage_logs')
    action = models.CharField(max_length=50, help_text="Action performed: 'price_check', 'order_place', etc.")
    endpoint = models.CharField(max_length=100, help_text="API endpoint or method called")
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True, help_text="Whether the action was successful")
    response_time = models.DecimalField(
        max_digits=8, 
        decimal_places=3, 
        help_text="Response time in seconds"
    )
    error_message = models.TextField(blank=True, null=True, help_text="Error message if failed")
    request_data = models.JSONField(
        blank=True, 
        null=True, 
        help_text="Request data (sanitized)"
    )
    response_data = models.JSONField(
        blank=True, 
        null=True, 
        help_text="Response data (sanitized)"
    )

    class Meta:
        db_table = 'api_key_usage_logs'
        verbose_name = 'API Key Usage Log'
        verbose_name_plural = 'API Key Usage Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['api_key', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
        ]

    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {self.api_key} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def log_usage(
        cls, 
        api_key: APIKey, 
        action: str, 
        endpoint: str, 
        success: bool, 
        response_time: float,
        error_message: str = None,
        request_data: dict = None,
        response_data: dict = None
    ):
        """Convenience method to log API key usage"""
        # Sanitize sensitive data from request/response
        sanitized_request = cls._sanitize_data(request_data) if request_data else None
        sanitized_response = cls._sanitize_data(response_data) if response_data else None
        
        return cls.objects.create(
            api_key=api_key,
            action=action,
            endpoint=endpoint,
            success=success,
            response_time=response_time,
            error_message=error_message,
            request_data=sanitized_request,
            response_data=sanitized_response
        )

    @staticmethod
    def _sanitize_data(data: dict) -> dict:
        """Remove sensitive information from log data"""
        if not data:
            return data
            
        sensitive_fields = ['api_key', 'secret_key', 'passphrase', 'password', 'token']
        sanitized = data.copy()
        
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***REDACTED***'
                
        return sanitized

    @classmethod
    def get_usage_statistics(cls, api_key: APIKey, days: int = 7) -> dict:
        """Get usage statistics for an API key"""
        from django.utils import timezone
        from django.db.models import Count, Avg, Q
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        stats = cls.objects.filter(
            api_key=api_key,
            timestamp__gte=start_date
        ).aggregate(
            total_requests=Count('id'),
            successful_requests=Count('id', filter=Q(success=True)),
            failed_requests=Count('id', filter=Q(success=False)),
            avg_response_time=Avg('response_time'),
            success_rate=Count('id', filter=Q(success=True)) * 100.0 / Count('id')
        )
        
        return stats