# backend/apps/risk_management/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone


User = get_user_model()

class RiskConfig(models.Model):
    """User-specific risk configuration"""
    RISK_TOLERANCE_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'), 
        ('high', 'High'),
        ('aggressive', 'Aggressive')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='risk_config')
    
    # Risk Tolerance
    risk_tolerance = models.CharField(
        max_length=20,
        choices=RISK_TOLERANCE_CHOICES,
        default='medium'
    )
    
    # Position Sizing
    max_position_size_usd = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('10000.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    max_position_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=10.00
    )
    
    # Loss Limits
    max_daily_loss_usd = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('2000.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    max_daily_loss_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=5.00
    )
    max_drawdown_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=15.00
    )
    
    # Trading Limits
    max_trades_per_day = models.IntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(1000)]
    )
    max_concurrent_trades = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    max_daily_volume = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('50000.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    min_profit_threshold = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.50,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Circuit Breakers
    enable_circuit_breaker = models.BooleanField(default=True)
    circuit_breaker_threshold = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Risk Monitoring
    volatility_threshold = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.00,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    liquidity_threshold = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=100000.00,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Trading Hours (if applicable)
    trading_hours_start = models.TimeField(null=True, blank=True)
    trading_hours_end = models.TimeField(null=True, blank=True)
    enable_trading_hours = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'risk_configs'
        verbose_name = 'Risk Configuration'
        verbose_name_plural = 'Risk Configurations'
    
    def __str__(self):
        return f"Risk Config - {self.user.username} ({self.risk_tolerance})"


class RiskMetrics(models.Model):
    """Daily risk metrics for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='risk_metrics')
    date = models.DateField()
    
    # Daily Trading Metrics
    daily_trades = models.IntegerField(default=0)
    daily_volume = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    daily_pnl = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    # Performance Metrics
    sharpe_ratio = models.DecimalField(
        max_digits=8, 
        decimal_places=4, 
        null=True, 
        blank=True
    )
    volatility = models.DecimalField(
        max_digits=8, 
        decimal_places=4, 
        null=True, 
        blank=True
    )
    max_drawdown = models.DecimalField(
        max_digits=8, 
        decimal_places=4, 
        null=True, 
        blank=True
    )
    
    # Additional Metrics
    win_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    average_profit = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        null=True, 
        blank=True
    )
    average_loss = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        null=True, 
        blank=True
    )
    
    # Risk Flags
    loss_breach = models.BooleanField(default=False)
    position_breach = models.BooleanField(default=False)
    volume_breach = models.BooleanField(default=False)
    circuit_breaker_triggered = models.BooleanField(default=False)
    
    # Compliance Flags
    trading_hours_violation = models.BooleanField(default=False)
    concentration_risk = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'risk_metrics'
        unique_together = ['user', 'date']
        verbose_name = 'Risk Metrics'
        verbose_name_plural = 'Risk Metrics'
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"Risk Metrics - {self.user.username} - {self.date}"


class TradeLimit(models.Model):
    """Trade limits and breaches"""
    LIMIT_TYPES = [
        ('daily_loss', 'Daily Loss'),
        ('position_size', 'Position Size'),
        ('concurrent_trades', 'Concurrent Trades'),
        ('daily_trades', 'Daily Trades'),
        ('daily_volume', 'Daily Volume'),
        ('max_drawdown', 'Maximum Drawdown'),
        ('volatility', 'Volatility'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trade_limits')
    limit_type = models.CharField(max_length=20, choices=LIMIT_TYPES)
    limit_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    current_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    is_breached = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    breached_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trade_limits'
        verbose_name = 'Trade Limit'
        verbose_name_plural = 'Trade Limits'
        indexes = [
            models.Index(fields=['user', 'is_breached']),
            models.Index(fields=['limit_type', 'is_active']),
        ]
    
    def __str__(self):
        status = "BREACHED" if self.is_breached else "ACTIVE"
        return f"{self.user.username} - {self.get_limit_type_display()} - {status}"


class RiskAlert(models.Model):
    """Risk alerts and notifications"""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    ALERT_TYPES = [
        ('position_size', 'Position Size Breach'),
        ('daily_loss', 'Daily Loss Breach'),
        ('drawdown', 'Max Drawdown Breach'),
        ('volatility', 'High Volatility'),
        ('liquidity', 'Low Liquidity'),
        ('circuit_breaker', 'Circuit Breaker Triggered'),
        ('trading_hours', 'Trading Hours Violation'),
        ('concentration', 'Concentration Risk'),
        ('volume_breach', 'Volume Limit Breach'),
        ('trade_limit', 'Trade Limit Breach'),
        ('arbitrage_opportunity', 'Arbitrage Opportunity'),
        ('trade_execution', 'Trade Execution Issue'),
        ('api_error', 'API Error'),
        ('connection_lost', 'Connection Lost'),
        ('system_health', 'System Health'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='risk_alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    message = models.TextField()
    metric = models.CharField(max_length=100, blank=True, null=True)
    value = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    threshold = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(blank=True, null=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    acknowledged_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='acknowledged_alerts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields for better alert management
    source = models.CharField(max_length=50, default='risk_management', help_text="Source system that generated the alert")
    context_data = models.JSONField(default=dict, blank=True, help_text="Additional context data for the alert")
    priority = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Alert priority (0-10, higher is more urgent)"
    )
    auto_resolve = models.BooleanField(default=False, help_text="Whether this alert can be auto-resolved")
    resolution_notes = models.TextField(blank=True, null=True, help_text="Notes on how the alert was resolved")
    
    class Meta:
        db_table = 'risk_alerts'
        verbose_name = 'Risk Alert'
        verbose_name_plural = 'Risk Alerts'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['severity', 'is_resolved']),
            models.Index(fields=['alert_type', 'created_at']),
            models.Index(fields=['is_resolved', 'acknowledged']),
            models.Index(fields=['source', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.get_severity_display()} - {self.user.username}"
    
    def mark_resolved(self, resolved_by=None, notes=None):
        """Mark alert as resolved with optional resolver and notes"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        if resolved_by:
            self.acknowledged_by = resolved_by
            self.acknowledged = True
            self.acknowledged_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        self.save()
    
    def acknowledge(self, acknowledged_by=None):
        """Acknowledge the alert without resolving it"""
        self.acknowledged = True
        self.acknowledged_at = timezone.now()
        if acknowledged_by:
            self.acknowledged_by = acknowledged_by
        self.save()
    
    def is_expired(self, hours=24):
        """Check if alert is older than specified hours"""
        expiration_time = self.created_at + timezone.timedelta(hours=hours)
        return timezone.now() > expiration_time
    
    def get_alert_summary(self):
        """Get a summary of the alert for notifications"""
        return {
            'id': self.id,
            'type': self.get_alert_type_display(),
            'severity': self.get_severity_display(),
            'message': self.message,
            'metric': self.metric,
            'value': float(self.value) if self.value else None,
            'threshold': float(self.threshold) if self.threshold else None,
            'created_at': self.created_at.isoformat(),
            'priority': self.priority
        }
    
    @property
    def duration(self):
        """Calculate how long the alert has been active"""
        if self.is_resolved and self.resolved_at:
            return self.resolved_at - self.created_at
        return timezone.now() - self.created_at
    
    @property
    def requires_immediate_attention(self):
        """Check if alert requires immediate attention"""
        return self.severity in ['high', 'critical'] and not self.acknowledged
    
    @classmethod
    def get_active_alerts(cls, user=None):
        """Get all active (unresolved) alerts, optionally filtered by user"""
        queryset = cls.objects.filter(is_resolved=False)
        if user:
            queryset = queryset.filter(user=user)
        return queryset
    
    @classmethod
    def get_critical_alerts(cls, user=None):
        """Get critical severity alerts"""
        queryset = cls.objects.filter(severity='critical', is_resolved=False)
        if user:
            queryset = queryset.filter(user=user)
        return queryset
    
    @classmethod
    def create_alert(cls, user, alert_type, severity, message, **kwargs):
        """Helper method to create alerts with common parameters"""
        return cls.objects.create(
            user=user,
            alert_type=alert_type,
            severity=severity,
            message=message,
            metric=kwargs.get('metric'),
            value=kwargs.get('value'),
            threshold=kwargs.get('threshold'),
            source=kwargs.get('source', 'risk_management'),
            priority=kwargs.get('priority', cls._calculate_priority(severity)),
            context_data=kwargs.get('context_data', {})
        )
    
    @classmethod
    def _calculate_priority(cls, severity):
        """Calculate priority based on severity"""
        priority_map = {
            'low': 1,
            'medium': 3,
            'high': 7,
            'critical': 10
        }
        return priority_map.get(severity, 0)

class CircuitBreakerLog(models.Model):
    """Log of circuit breaker activations"""
    TRIGGER_TYPES = [
        ('daily_loss', 'Daily Loss'),
        ('drawdown', 'Maximum Drawdown'),
        ('volatility', 'High Volatility'),
        ('manual', 'Manual Intervention'),
        ('system', 'System Trigger'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='circuit_breaker_logs')
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    trigger_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    threshold = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(auto_now_add=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'circuit_breaker_logs'
        verbose_name = 'Circuit Breaker Log'
        verbose_name_plural = 'Circuit Breaker Logs'
        indexes = [
            models.Index(fields=['user', 'activated_at']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        status = "ACTIVE" if self.is_active else "INACTIVE"
        return f"Circuit Breaker - {self.user.username} - {self.trigger_type} - {status}"


class RiskReport(models.Model):
    """Periodic risk reports"""
    REPORT_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('ad_hoc', 'Ad Hoc'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='risk_reports')
    report_type = models.CharField(max_length=10, choices=REPORT_TYPES)
    period_start = models.DateField()
    period_end = models.DateField()
    report_data = models.JSONField()  # Stores comprehensive risk metrics
    summary = models.TextField()
    recommendations = models.TextField(blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'risk_reports'
        verbose_name = 'Risk Report'
        verbose_name_plural = 'Risk Reports'
        indexes = [
            models.Index(fields=['user', 'period_start']),
            models.Index(fields=['report_type', 'generated_at']),
        ]
        ordering = ['-period_start']
    
    def __str__(self):
        return f"Risk Report - {self.user.username} - {self.report_type} - {self.period_start}"