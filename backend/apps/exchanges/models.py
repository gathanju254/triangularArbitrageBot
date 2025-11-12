# backend/apps/exchanges/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Exchange(models.Model):
    EXCHANGE_TYPES = [
        ('cex', 'Centralized Exchange'),
        ('dex', 'Decentralized Exchange'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)  # e.g., 'binance', 'coinbase', 'okx'
    exchange_type = models.CharField(max_length=10, choices=EXCHANGE_TYPES, default='cex')
    base_url = models.URLField()
    api_documentation = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    trading_fee = models.DecimalField(max_digits=6, decimal_places=4, default=0.001)  # 0.1%
    withdrawal_fee = models.JSONField(default=dict)  # Store fees for different currencies
    rate_limit = models.IntegerField(default=1200)  # Requests per minute
    precision_info = models.JSONField(default=dict)  # Price, amount precision
    supported_pairs = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'exchanges'
        verbose_name = 'Exchange'
        verbose_name_plural = 'Exchanges'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class MarketData(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=20)  # e.g., 'BTC/USDT'
    bid_price = models.DecimalField(max_digits=20, decimal_places=8)
    ask_price = models.DecimalField(max_digits=20, decimal_places=8)
    last_price = models.DecimalField(max_digits=20, decimal_places=8)
    volume_24h = models.DecimalField(max_digits=20, decimal_places=8)
    spread = models.DecimalField(max_digits=10, decimal_places=4)  # Percentage
    timestamp = models.DateTimeField()
    is_fresh = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'market_data'
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['exchange', 'symbol']),
        ]
        verbose_name = 'Market Data'
        verbose_name_plural = 'Market Data'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.exchange.code} - {self.symbol} - {self.timestamp}"


class ExchangeCredentials(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    api_key = models.ForeignKey('users.APIKey', on_delete=models.CASCADE)
    is_validated = models.BooleanField(default=False)
    validation_message = models.TextField(blank=True, null=True)
    last_validation = models.DateTimeField(null=True, blank=True)
    trading_enabled = models.BooleanField(default=False)
    withdrawal_enabled = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'exchange_credentials'
        unique_together = ['user', 'exchange']
        verbose_name = 'Exchange Credentials'
        verbose_name_plural = 'Exchange Credentials'

    def validate_credentials(self):
        """
        Validate exchange credentials using the CredentialsService.
        This method is called from signals and views.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Import here to avoid circular imports
            from .services import CredentialsService
            
            logger.info(f"🔐 Validating credentials for {self.exchange.name} (User: {self.user.username})")
            
            credentials_service = CredentialsService(self)
            is_valid = credentials_service.validate_credentials()
            
            # The service already updates the instance, but we'll log the result
            if is_valid:
                logger.info(f"✅ Credentials validated successfully for {self.exchange.name}")
            else:
                logger.warning(f"❌ Credentials validation failed for {self.exchange.name}")
            
            return is_valid
            
        except ImportError as e:
            logger.error(f"🔧 Import error in validate_credentials: {str(e)}")
            self._handle_validation_error(f"Service unavailable: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"💥 Unexpected error validating credentials for {self.exchange.name}: {str(e)}")
            self._handle_validation_error(f"Validation error: {str(e)}")
            return False

    def _handle_validation_error(self, error_message):
        """Helper method to handle validation errors consistently"""
        self.is_validated = False
        self.validation_message = error_message
        self.last_validation = timezone.now()
        self.save(update_fields=['is_validated', 'validation_message', 'last_validation'])

    def test_connection(self):
        """
        Test connection without updating validation status.
        Useful for quick connectivity checks.
        """
        try:
            from .services import ExchangeService
            
            exchange_service = ExchangeService(self.exchange_id, self)
            
            # Try a lightweight operation to test connectivity
            status_info = exchange_service.get_exchange_status()
            return status_info.get('is_online', False)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Connection test failed for {self.exchange.name}: {str(e)}")
            return False

    def mark_as_validated(self, is_valid=True, message=None):
        """
        Helper method to mark credentials as validated without full validation.
        Useful for manual overrides or testing.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        self.is_validated = is_valid
        self.last_validation = timezone.now()
        
        if message:
            self.validation_message = message
        elif is_valid:
            self.validation_message = "Credentials validated successfully"
        else:
            self.validation_message = "Credentials validation failed"
        
        try:
            self.save(update_fields=['is_validated', 'validation_message', 'last_validation'])
            logger.info(f"📝 Credentials manually marked as {'valid' if is_valid else 'invalid'} for {self.exchange.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save validation status for {self.exchange.name}: {str(e)}")
            return False

    def enable_trading(self):
        """Enable trading for this exchange"""
        self.trading_enabled = True
        self.save(update_fields=['trading_enabled'])

    def disable_trading(self):
        """Disable trading for this exchange"""
        self.trading_enabled = False
        self.save(update_fields=['trading_enabled'])

    def can_trade(self):
        """Check if trading is allowed (validated and enabled)"""
        return self.is_validated and self.trading_enabled

    def can_withdraw(self):
        """Check if withdrawal is allowed (validated and enabled)"""
        return self.is_validated and self.withdrawal_enabled

    def get_validation_status(self):
        """Get detailed validation status"""
        return {
            'is_validated': self.is_validated,
            'validation_message': self.validation_message,
            'last_validation': self.last_validation,
            'trading_enabled': self.trading_enabled,
            'withdrawal_enabled': self.withdrawal_enabled,
            'can_trade': self.can_trade(),
            'can_withdraw': self.can_withdraw()
        }

    def __str__(self):
        return f"{self.user.username} - {self.exchange.name} ({'Validated' if self.is_validated else 'Invalid'})"