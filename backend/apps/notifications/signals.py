# backend/apps/notifications/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Notification
from .tasks import send_email_notification

# Import TAB-specific models (use conditional imports to avoid errors)
try:
    from apps.arbitrage_bot.models.trade import TradeRecord
    from apps.arbitrage_bot.models.arbitrage_opportunity import ArbitrageOpportunityRecord
    TAB_MODELS_AVAILABLE = True
except ImportError:
    TAB_MODELS_AVAILABLE = False
    print("TAB models not available - notifications will work with basic functionality")

# Risk alerts model - create if doesn't exist
try:
    from apps.arbitrage_bot.models.risk_alert import RiskAlert
    RISK_MODELS_AVAILABLE = True
except ImportError:
    RISK_MODELS_AVAILABLE = False
    print("RiskAlert model not available")

@receiver(post_save, sender=TradeRecord)
def create_trade_notification(sender, instance, created, **kwargs):
    """Create notification for trade execution events in TAB"""
    if not TAB_MODELS_AVAILABLE:
        return
        
    if created:
        # Determine notification type based on trade profit
        notification_type = 'trade'
        priority = 'medium'
        
        if instance.profit > 0:
            title = "SUCCESS - Profitable Trade Executed"
            message = f"Trade completed with ${instance.profit:.2f} profit ({instance.profit_percentage:.2f}%)"
        else:
            title = "WARNING - Trade Completed with Loss"
            message = f"Trade completed with ${abs(instance.profit):.2f} loss ({instance.profit_percentage:.2f}%)"
            priority = 'high'
        
        # Get user from request context or use system user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            # Try to get the first admin user or create system notification
            user = User.objects.filter(is_staff=True).first()
            if not user:
                user = User.objects.first()
            
            if user:
                notification = Notification.objects.create(
                    user=user,
                    notification_type=notification_type,
                    priority=priority,
                    title=title,
                    message=message,
                    data={
                        'trade_id': instance.id,
                        'profit': float(instance.profit),
                        'profit_percentage': float(instance.profit_percentage),
                        'exchange': instance.exchange,
                        'timestamp': instance.timestamp.isoformat() if instance.timestamp else None
                    },
                    delivery_methods=['in_app']
                )
                
                # Send email for high priority notifications
                if priority == 'high':
                    notification.delivery_methods.append('email')
                    notification.save()
                    send_email_notification.delay(notification.id)
                    
        except Exception as e:
            print(f"Error creating trade notification: {e}")

@receiver(post_save, sender=ArbitrageOpportunityRecord)
def create_arbitrage_notification(sender, instance, created, **kwargs):
    """Create notification for arbitrage opportunities in TAB"""
    if not TAB_MODELS_AVAILABLE:
        return
        
    if created:
        # Only notify for high-profit opportunities
        profit_threshold = 1.0  # 1% minimum profit
        
        if instance.profit_percentage >= profit_threshold:
            priority = 'high' if instance.profit_percentage >= 3.0 else 'medium'
            
            # Get user from request context or use system user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            try:
                user = User.objects.filter(is_staff=True).first()
                if not user:
                    user = User.objects.first()
                
                if user:
                    triangle_str = ' → '.join(instance.triangle) if isinstance(instance.triangle, list) else str(instance.triangle)
                    
                    notification = Notification.objects.create(
                        user=user,
                        notification_type='opportunity',
                        priority=priority,
                        title="ARBITRAGE - Opportunity Detected",
                        message=f"{triangle_str}: {instance.profit_percentage:.2f}% profit opportunity",
                        data={
                            'opportunity_id': instance.id,
                            'profit_percentage': float(instance.profit_percentage),
                            'triangle': instance.triangle,
                            'timestamp': instance.timestamp.isoformat() if instance.timestamp else None
                        },
                        delivery_methods=['in_app', 'email']
                    )
                    
                    send_email_notification.delay(notification.id)
                    
            except Exception as e:
                print(f"Error creating arbitrage notification: {e}")

# Create a simple RiskAlert model if it doesn't exist
if not RISK_MODELS_AVAILABLE:
    try:
        from django.db import models
        from django.contrib.auth import get_user_model
        
        class RiskAlert(models.Model):
            user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
            alert_type = models.CharField(max_length=50)
            severity = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')])
            message = models.TextField()
            metric = models.CharField(max_length=100, blank=True, null=True)
            value = models.FloatField(blank=True, null=True)
            threshold = models.FloatField(blank=True, null=True)
            created_at = models.DateTimeField(auto_now_add=True)
            
            class Meta:
                db_table = 'risk_alerts'
                
            def __str__(self):
                return f"RiskAlert {self.id} - {self.alert_type} - {self.severity}"
                
        RISK_MODELS_AVAILABLE = True
        print("Created RiskAlert model for notifications")
    except Exception as e:
        print(f"Could not create RiskAlert model: {e}")

@receiver(post_save, sender=RiskAlert)
def create_risk_notification(sender, instance, created, **kwargs):
    """Create notification for risk alerts"""
    if not RISK_MODELS_AVAILABLE:
        return
        
    if created:
        priority_map = {
            'low': 'low',
            'medium': 'medium', 
            'high': 'high',
            'critical': 'critical'
        }
        
        notification = Notification.objects.create(
            user=instance.user,
            notification_type='risk',
            priority=priority_map.get(instance.severity, 'medium'),
            title=f"RISK ALERT: {instance.alert_type}",
            message=instance.message,
            data={
                'alert_id': instance.id,
                'alert_type': instance.alert_type,
                'severity': instance.severity,
                'metric': instance.metric,
                'value': float(instance.value) if instance.value else None,
                'threshold': float(instance.threshold) if instance.threshold else None
            },
            delivery_methods=['in_app', 'email']
        )
        
        send_email_notification.delay(notification.id)

@receiver(pre_save, sender=Notification)
def update_notification_timestamps(sender, instance, **kwargs):
    """Update read_at timestamp when notification is marked as read"""
    if instance.pk:
        try:
            old_instance = Notification.objects.get(pk=instance.pk)
            if not old_instance.is_read and instance.is_read:
                instance.read_at = timezone.now()
            elif old_instance.is_read and not instance.is_read:
                instance.read_at = None
        except Notification.DoesNotExist:
            pass

# System-wide notifications for important events
def create_system_notification(title, message, priority='medium', data=None):
    """Helper function to create system notifications"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        # Send to all admin users
        admin_users = User.objects.filter(is_staff=True)
        for user in admin_users:
            Notification.objects.create(
                user=user,
                notification_type='system',
                priority=priority,
                title=title,
                message=message,
                data=data or {},
                delivery_methods=['in_app']
            )
    except Exception as e:
        print(f"Error creating system notification: {e}")

# Bot status notifications
def create_bot_status_notification(status, message, data=None):
    """Create notification for bot status changes"""
    title_map = {
        'started': 'BOT STARTED - Triangular Arbitrage Bot',
        'stopped': 'BOT STOPPED - Triangular Arbitrage Bot', 
        'error': 'BOT ERROR - Triangular Arbitrage Bot',
        'warning': 'BOT WARNING - Triangular Arbitrage Bot'
    }
    
    priority_map = {
        'started': 'medium',
        'stopped': 'medium',
        'error': 'high',
        'warning': 'medium'
    }
    
    title = title_map.get(status, f"BOT {status.upper()} - Triangular Arbitrage Bot")
    priority = priority_map.get(status, 'medium')
    
    create_system_notification(
        title=title,
        message=message,
        priority=priority,
        data=data or {'bot_status': status}
    )

# Exchange connection notifications
def create_exchange_notification(exchange, status, message, data=None):
    """Create notification for exchange connection events"""
    title_map = {
        'connected': f'EXCHANGE CONNECTED - {exchange.upper()}',
        'disconnected': f'EXCHANGE DISCONNECTED - {exchange.upper()}',
        'error': f'EXCHANGE ERROR - {exchange.upper()}',
        'reconnected': f'EXCHANGE RECONNECTED - {exchange.upper()}'
    }
    
    priority_map = {
        'connected': 'medium',
        'disconnected': 'high',
        'error': 'high',
        'reconnected': 'medium'
    }
    
    title = title_map.get(status, f"EXCHANGE {status.upper()} - {exchange.upper()}")
    priority = priority_map.get(status, 'medium')
    
    create_system_notification(
        title=title,
        message=message,
        priority=priority,
        data=data or {'exchange': exchange, 'connection_status': status}
    )

# Trading notifications
def create_trading_notification(trade_type, symbol, profit=None, amount=None, data=None):
    """Create notification for trading events"""
    if trade_type == 'manual_trade':
        title = "MANUAL TRADE EXECUTED"
        message = f"Manual trade executed for {symbol}"
        if amount:
            message += f" - Amount: ${amount:.2f}"
        if profit is not None:
            message += f" - Profit: ${profit:.4f}"
    elif trade_type == 'auto_trade':
        title = "AUTO TRADE EXECUTED"
        message = f"Auto trade executed for {symbol}"
        if amount:
            message += f" - Amount: ${amount:.2f}"
        if profit is not None:
            message += f" - Profit: ${profit:.4f}"
    else:
        title = f"TRADING EVENT - {trade_type.upper()}"
        message = f"Trading event for {symbol}"
    
    priority = 'high' if profit and profit > 0 else 'medium'
    
    create_system_notification(
        title=title,
        message=message,
        priority=priority,
        data=data or {
            'trade_type': trade_type,
            'symbol': symbol,
            'profit': profit,
            'amount': amount
        }
    )

# Risk management notifications
def create_risk_notification(risk_type, metric, value, threshold, message, data=None):
    """Create notification for risk management events"""
    priority_map = {
        'limit_exceeded': 'high',
        'threshold_breached': 'medium',
        'warning': 'medium',
        'critical': 'critical'
    }
    
    title = f"RISK MANAGEMENT - {risk_type.replace('_', ' ').title()}"
    priority = priority_map.get(risk_type, 'medium')
    
    notification_data = {
        'risk_type': risk_type,
        'metric': metric,
        'value': value,
        'threshold': threshold
    }
    if data:
        notification_data.update(data)
    
    create_system_notification(
        title=title,
        message=message,
        priority=priority,
        data=notification_data
    )