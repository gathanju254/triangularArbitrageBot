# backend/apps/risk_management/tasks.py
import logging
from decimal import Decimal
from celery import shared_task
from django.utils import timezone
from .services import LimitMonitoringService
from .models import RiskMetrics, TradeLimit

logger = logging.getLogger(__name__)

@shared_task
def reset_daily_limits():
    """Reset daily trading limits (run at midnight)"""
    try:
        logger.info("Starting daily limits reset task")
        LimitMonitoringService.reset_daily_limits()
        logger.info("Daily limits reset completed successfully")
    except Exception as e:
        logger.error(f"Error resetting daily limits: {e}")
        raise

@shared_task
def calculate_daily_risk_metrics():
    """Calculate daily risk metrics for all active users"""
    from apps.users.models import User
    
    try:
        today = timezone.now().date()
        active_users = User.objects.filter(is_active=True)
        
        logger.info(f"Calculating daily risk metrics for {active_users.count()} active users")
        
        for user in active_users:
            try:
                # Calculate risk metrics
                sharpe_ratio = calculate_sharpe_ratio(user)
                volatility = calculate_volatility(user)
                max_drawdown = calculate_max_drawdown(user)
                
                # Update or create risk metrics
                RiskMetrics.objects.update_or_create(
                    user=user,
                    date=today,
                    defaults={
                        'sharpe_ratio': sharpe_ratio,
                        'volatility': volatility,
                        'max_drawdown': max_drawdown
                    }
                )
                
                logger.debug(f"Updated risk metrics for user {user.id}")
                
            except Exception as user_error:
                logger.error(f"Error calculating metrics for user {user.id}: {user_error}")
                continue
        
        logger.info("Daily risk metrics calculation completed")
        
    except Exception as e:
        logger.error(f"Error in calculate_daily_risk_metrics task: {e}")
        raise

@shared_task
def monitor_risk_limits():
    """Monitor and alert on risk limit breaches"""
    try:
        breached_limits = TradeLimit.objects.filter(is_breached=True, is_active=True)
        
        logger.info(f"Monitoring {breached_limits.count()} breached risk limits")
        
        for limit in breached_limits:
            try:
                # Import here to avoid circular imports
                from apps.notifications.services import NotificationService
                
                NotificationService.send_risk_alert(
                    user=limit.user,
                    message=f"Risk limit breached: {limit.limit_type} - Current: {limit.current_value}, Limit: {limit.limit_value}",
                    level="high"
                )
                
                logger.info(f"Sent risk alert for user {limit.user.id} - {limit.limit_type}")
                
            except Exception as limit_error:
                logger.error(f"Error sending alert for limit {limit.id}: {limit_error}")
                continue
                
    except Exception as e:
        logger.error(f"Error in monitor_risk_limits task: {e}")
        raise

@shared_task
def update_risk_metrics_for_user(user_id):
    """Update risk metrics for a specific user"""
    from apps.users.models import User
    
    try:
        user = User.objects.get(id=user_id)
        today = timezone.now().date()
        
        logger.info(f"Updating risk metrics for user {user_id}")
        
        # Calculate risk metrics
        sharpe_ratio = calculate_sharpe_ratio(user)
        volatility = calculate_volatility(user)
        max_drawdown = calculate_max_drawdown(user)
        
        # Update or create risk metrics
        RiskMetrics.objects.update_or_create(
            user=user,
            date=today,
            defaults={
                'sharpe_ratio': sharpe_ratio,
                'volatility': volatility,
                'max_drawdown': max_drawdown
            }
        )
        
        logger.info(f"Successfully updated risk metrics for user {user_id}")
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found")
    except Exception as e:
        logger.error(f"Error updating risk metrics for user {user_id}: {e}")
        raise

@shared_task
def cleanup_old_risk_metrics(days_old=30):
    """Clean up risk metrics older than specified days"""
    try:
        cutoff_date = timezone.now().date() - timezone.timedelta(days=days_old)
        deleted_count = RiskMetrics.objects.filter(date__lt=cutoff_date).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} risk metrics records older than {days_old} days")
        
    except Exception as e:
        logger.error(f"Error cleaning up old risk metrics: {e}")
        raise

@shared_task
def sync_user_risk_configs():
    """Ensure all active users have risk configurations"""
    from apps.users.models import User
    from .models import RiskConfig
    
    try:
        active_users = User.objects.filter(is_active=True)
        configs_created = 0
        
        for user in active_users:
            # Create default risk config if it doesn't exist
            config, created = RiskConfig.objects.get_or_create(
                user=user,
                defaults={
                    'max_position_size_usd': Decimal('5000.00'),
                    'max_trades_per_day': 50,
                    'max_daily_volume': Decimal('10000.00'),
                    'max_daily_loss': Decimal('500.00'),
                    'risk_tolerance': 'medium'
                }
            )
            
            if created:
                configs_created += 1
                logger.debug(f"Created default risk config for user {user.id}")
        
        logger.info(f"Risk config sync completed. Created {configs_created} new configurations")
        
    except Exception as e:
        logger.error(f"Error syncing user risk configs: {e}")
        raise

def calculate_sharpe_ratio(user):
    """Calculate Sharpe ratio for user's portfolio"""
    try:
        # TODO: Implement actual Sharpe ratio calculation
        # This should consider:
        # - Portfolio returns
        # - Risk-free rate
        # - Portfolio standard deviation
        
        # Placeholder implementation - replace with actual calculation
        # Example: (Portfolio Return - Risk Free Rate) / Portfolio Standard Deviation
        
        # For now, return a realistic placeholder value
        return Decimal('1.2')  # Example: 1.2 Sharpe ratio
        
    except Exception as e:
        logger.error(f"Error calculating Sharpe ratio for user {user.id}: {e}")
        return Decimal('0.0')

def calculate_volatility(user):
    """Calculate portfolio volatility (standard deviation of returns)"""
    try:
        # TODO: Implement actual volatility calculation
        # This should consider:
        # - Historical returns data
        # - Standard deviation calculation
        # - Time period (e.g., 30-day volatility)
        
        # Placeholder implementation
        # Example: Calculate standard deviation of daily returns over 30 days
        
        return Decimal('0.18')  # Example: 18% volatility
        
    except Exception as e:
        logger.error(f"Error calculating volatility for user {user.id}: {e}")
        return Decimal('0.0')

def calculate_max_drawdown(user):
    """Calculate maximum drawdown for user's portfolio"""
    try:
        # TODO: Implement actual max drawdown calculation
        # This should consider:
        # - Portfolio value history
        # - Peak to trough declines
        # - Maximum percentage decline
        
        # Placeholder implementation
        # Example: (Peak Value - Trough Value) / Peak Value
        
        return Decimal('0.08')  # Example: 8% maximum drawdown
        
    except Exception as e:
        logger.error(f"Error calculating max drawdown for user {user.id}: {e}")
        return Decimal('0.0')