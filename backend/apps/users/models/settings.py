# backend/apps/users/models/settings.py
from django.db import models
from django.forms import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class UserSettings(models.Model):
    """Centralized user settings model"""
    
    user = models.OneToOneField(
        'users.User', 
        on_delete=models.CASCADE, 
        related_name='settings'
    )
    
    # === TRADING SETTINGS ===
    AUTO_TRADING_MODES = [
        ('manual', 'Manual Confirmation'),
        ('semi_auto', 'Semi-Auto (Confirm Large Trades)'),
        ('full_auto', 'Full Auto (No Confirmation)'),
    ]
    
    trading_mode = models.CharField(
        max_length=20, 
        choices=AUTO_TRADING_MODES, 
        default='manual'
    )
    max_concurrent_trades = models.IntegerField(default=3)
    min_trade_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=10.00,
        validators=[MinValueValidator(1.01)]  # Must be > $1
    )
    slippage_tolerance = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.1,
        validators=[MinValueValidator(0.01), MaxValueValidator(5.0)]
    )
    
    # === RISK MANAGEMENT SETTINGS ===
    RISK_TOLERANCE_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    risk_tolerance = models.CharField(
        max_length=20,
        choices=RISK_TOLERANCE_CHOICES,
        default='medium'
    )
    max_daily_loss = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1000.00
    )
    max_position_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=5000.00
    )
    max_drawdown = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=20.0
    )
    stop_loss_enabled = models.BooleanField(default=True)
    take_profit_enabled = models.BooleanField(default=True)
    stop_loss_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=2.0
    )
    take_profit_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.0
    )
    
    # === NOTIFICATION SETTINGS ===
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)
    trading_alerts = models.BooleanField(default=True)
    risk_alerts = models.BooleanField(default=True)
    
    # === EXCHANGE SETTINGS ===
    preferred_exchanges = models.JSONField(default=list)
    min_profit_threshold = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.3
    )
    
    # === AUDIT FIELDS ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_modified_by = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='modified_settings'
    )
    
    class Meta:
        db_table = 'user_settings'
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'
    
    def __str__(self):
        return f"Settings for {self.user.username}"
    
    def clean(self):
        """Validate settings constraints"""
        if self.min_trade_amount <= 1.00:
            raise ValidationError({
                'min_trade_amount': 'Minimum trade amount must be greater than $1.00'
            })
        
        if self.stop_loss_percent <= 0:
            raise ValidationError({
                'stop_loss_percent': 'Stop loss percentage must be positive'
            })
        
        if self.take_profit_percent <= 0:
            raise ValidationError({
                'take_profit_percent': 'Take profit percentage must be positive'
            })


class BotConfiguration(models.Model):
    """System-wide bot configuration (singleton)"""
    
    # === TRADING CONFIGURATION ===
    base_balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1000.00
    )
    trade_size_fraction = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        default=0.01,  # 1% of base balance
        validators=[MinValueValidator(0.0001), MaxValueValidator(1.0)]
    )
    auto_restart = models.BooleanField(default=True)
    trading_enabled = models.BooleanField(default=False)
    
    # === SYSTEM SETTINGS ===
    enabled_exchanges = models.JSONField(default=list)
    health_check_interval = models.IntegerField(default=300)  # 5 minutes
    data_retention_days = models.IntegerField(default=30)
    
    # === AUDIT FIELDS ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bot_configuration'
        verbose_name = 'Bot Configuration'
        verbose_name_plural = 'Bot Configuration'
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        if not self.pk and BotConfiguration.objects.exists():
            # Update existing instance instead of creating new one
            existing = BotConfiguration.objects.first()
            existing.base_balance = self.base_balance
            existing.trade_size_fraction = self.trade_size_fraction
            existing.auto_restart = self.auto_restart
            existing.trading_enabled = self.trading_enabled
            existing.enabled_exchanges = self.enabled_exchanges
            existing.health_check_interval = self.health_check_interval
            existing.data_retention_days = self.data_retention_days
            return existing.save(*args, **kwargs)
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj