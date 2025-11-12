# tudollar/backend/apps/arbitrage/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import ArbitrageOpportunity, TradeExecution
from apps.notifications.services import NotificationService

@receiver(post_save, sender=ArbitrageOpportunity)
def handle_new_opportunity(sender, instance, created, **kwargs):
    """Handle new arbitrage opportunity detection"""
    if created and instance.profit_percentage >= instance.MIN_PROFIT_THRESHOLD:
        # Send real-time notification
        NotificationService.send_opportunity_alert(instance)
        
        # Log opportunity for analytics
        from .tasks import log_opportunity_analytics
        log_opportunity_analytics.delay(instance.id)

@receiver(post_save, sender=TradeExecution)
def handle_trade_execution(sender, instance, created, **kwargs):
    """Handle trade execution updates"""
    if instance.status == TradeExecution.Status.COMPLETED:
        # Update user balance and PnL
        from .tasks import update_user_portfolio
        update_user_portfolio.delay(instance.id)
        
        # Send trade completion notification
        NotificationService.send_trade_completion_alert(instance)