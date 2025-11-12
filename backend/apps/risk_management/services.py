# backend/apps/risk_management/services.py

import logging
from decimal import Decimal
from typing import Tuple, Dict, Any, Optional, List

from django.utils import timezone
from django.db import transaction
from django.core.cache import cache

from .models import RiskConfig, RiskMetrics, TradeLimit
from .engines.compliance_checker import ComplianceChecker
from .engines.circuit_breaker import CircuitBreaker
from .engines.risk_calculator import RiskCalculator

logger = logging.getLogger(__name__)


class RiskService:
    """
    Lightweight service used by permissions and trading services to
    check whether a proposed trade/order complies with user's risk limits.
    Used by `core.permissions.RiskPermission` and trading code.
    """

    def __init__(self, user):
        self.user = user
        self.risk_config = self._get_risk_config()
        self._circuit = CircuitBreaker()
        self._checker = ComplianceChecker(self.risk_config) if self.risk_config else None

    def _get_risk_config(self) -> Optional[RiskConfig]:
        """Safely get risk config with fallback to default configuration"""
        try:
            config, created = RiskConfig.objects.get_or_create(
                user=self.user,
                defaults=self._get_default_risk_config()
            )
            if created:
                logger.info("Created default risk config for user %s", getattr(self.user, "id", None))
            return config
        except Exception as exc:
            logger.error("Error getting risk config for user %s: %s", getattr(self.user, "id", None), exc)
            return None

    def _get_default_risk_config(self) -> Dict[str, Any]:
        """Default risk parameters for new users"""
        return {
            'max_position_size_usd': Decimal('5000.00'),
            'max_trades_per_day': 50,
            'max_daily_loss_usd': Decimal('500.00'),
            'max_daily_volume': Decimal('25000.00'),
            'risk_tolerance': 'medium',
            'require_2fa': False,
            'auto_hedge_enabled': False
        }

    def check_trade_permission(self, order_data: Dict[str, Any]) -> bool:
        """
        Return True if the trade described by `order_data` is allowed.
        Expected keys in order_data: amount, price (optional), symbol, order_type, side.
        """
        try:
            # If no config found, deny by default for safety
            if not self.risk_config:
                logger.warning("No RiskConfig for user %s - denying trade", getattr(self.user, "id", None))
                return False

            # Circuit breaker
            if self._circuit.is_triggered(self.user):
                logger.info("Circuit breaker triggered for user %s", getattr(self.user, "id", None))
                return False

            # Compute notional / position size (USD). If price missing, assume 1.
            amount = Decimal(str(order_data.get("amount", "0")))
            price = Decimal(str(order_data.get("price", "1"))) if order_data.get("price") is not None else Decimal("1")
            position_size = amount * price

            # Max position size check
            if position_size > self.risk_config.max_position_size_usd:
                logger.info("Position size %.2f exceeds max %.2f for user %s", 
                           position_size, self.risk_config.max_position_size_usd, 
                           getattr(self.user, "id", None))
                return False

            # Daily trades check (use RiskMetrics if available)
            today = timezone.now().date()
            metrics = RiskMetrics.objects.filter(user=self.user, date=today).first()
            if metrics and metrics.daily_trades >= self.risk_config.max_trades_per_day:
                logger.info("Daily trade limit reached for user %s", getattr(self.user, "id", None))
                return False

            # Daily volume check
            if metrics and (metrics.daily_volume + position_size) > self.risk_config.max_daily_volume:
                logger.info("Daily volume limit exceeded for user %s", getattr(self.user, "id", None))
                return False

            # Use compliance checker for additional checks
            if self._checker:
                ok, message = self._checker._check_concurrent_trades()
                if not ok:
                    logger.info("Compliance check failed: %s", message)
                    return False

                ok_cb, msg_cb = self._checker._check_circuit_breaker()
                if not ok_cb:
                    logger.info("Compliance circuit breaker check failed: %s", msg_cb)
                    return False

            return True

        except Exception as exc:
            logger.exception("Error while checking trade permission: %s", exc)
            # Fail safe: deny on unexpected errors
            return False

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary for the user"""
        if not self.risk_config:
            return {"error": "No risk configuration found"}
        
        today = timezone.now().date()
        metrics = RiskMetrics.objects.filter(user=self.user, date=today).first()
        
        return {
            "user_id": self.user.id,
            "risk_config": {
                "max_position_size_usd": float(self.risk_config.max_position_size_usd),
                "max_trades_per_day": self.risk_config.max_trades_per_day,
                "max_daily_loss_usd": float(self.risk_config.max_daily_loss_usd),
                "max_daily_volume": float(self.risk_config.max_daily_volume),
                "risk_tolerance": self.risk_config.risk_tolerance,
            },
            "daily_metrics": {
                "trades": metrics.daily_trades if metrics else 0,
                "volume": float(metrics.daily_volume) if metrics else 0.0,
                "pnl": float(metrics.daily_pnl) if metrics else 0.0,
            } if metrics else None,
            "remaining_limits": {
                "trades": max(0, self.risk_config.max_trades_per_day - (metrics.daily_trades if metrics else 0)),
                "volume": float(max(Decimal('0'), self.risk_config.max_daily_volume - (metrics.daily_volume if metrics else Decimal('0')))),
            }
        }


class RiskManagementService:
    """
    Higher-level service used by views/tasks/other app services.
    Provides richer responses (is_compliant, message) and helper utilities.
    """

    @staticmethod
    def check_trade_compliance(user, trade_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check trade compliance and return (is_compliant, message).
        This is used by `apps.arbitrage.services.TradeExecutionService` and by risk endpoints.
        """
        try:
            risk_service = RiskService(user)
            allowed = risk_service.check_trade_permission(trade_data)
            return (allowed, "" if allowed else "Trade violates risk limits or circuit breaker is active")
        except Exception as exc:
            logger.exception("Error checking trade compliance for user %s: %s", getattr(user, "id", None), exc)
            return False, "Internal error while validating trade against risk rules"

    @staticmethod
    def get_user_risk_overview(user) -> Dict[str, Any]:
        """
        Return a summary of a user's current risk state (limits, breached counts, score).
        """
        cache_key = f"risk_overview_{user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        try:
            config = RiskConfig.objects.filter(user=user).first()
            today = timezone.now().date()
            metrics = RiskMetrics.objects.filter(user=user, date=today).first()
            active_limits = TradeLimit.objects.filter(user=user).count()
            breached = TradeLimit.objects.filter(user=user, is_breached=True).count()

            calculator = RiskCalculator()
            score = calculator.calculate_portfolio_risk(user) if config else Decimal("0.0")

            risk_overview = {
                "config": {
                    "max_position_size_usd": float(config.max_position_size_usd) if config else 5000.0,
                    "max_trades_per_day": config.max_trades_per_day if config else 50,
                    "max_daily_loss_usd": float(config.max_daily_loss_usd) if config else 500.0,
                    "max_daily_volume": float(config.max_daily_volume) if config else 25000.0,
                    "risk_tolerance": config.risk_tolerance if config else "medium",
                } if config else {},
                "today_metrics": {
                    "daily_trades": metrics.daily_trades if metrics else 0,
                    "daily_volume": float(metrics.daily_volume) if metrics else 0.0,
                    "daily_pnl": float(metrics.daily_pnl) if metrics else 0.0,
                } if metrics else {},
                "active_limits": active_limits,
                "breached_limits": breached,
                "risk_score": float(score) if isinstance(score, Decimal) else score,
                "remaining_daily_trades": max(0, config.max_trades_per_day - (metrics.daily_trades if metrics else 0)) if config else 0,
                "remaining_daily_volume": float(max(Decimal('0'), config.max_daily_volume - (metrics.daily_volume if metrics else Decimal('0')))) if config else 0.0,
                "timestamp": timezone.now().isoformat()
            }
            
            # Cache for 2 minutes
            cache.set(cache_key, risk_overview, 120)
            return risk_overview
            
        except Exception as exc:
            logger.exception("Failed to build risk overview for user %s: %s", getattr(user, "id", None), exc)
            return {
                "config": {},
                "today_metrics": {},
                "active_limits": 0,
                "breached_limits": 0,
                "risk_score": 0,
                "remaining_daily_trades": 0,
                "remaining_daily_volume": 0.0,
                "error": "Failed to load risk overview"
            }

    @staticmethod
    def update_risk_config(user, config_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update user risk configuration with validation
        """
        try:
            with transaction.atomic():
                config, created = RiskConfig.objects.get_or_create(
                    user=user,
                    defaults=RiskManagementService._get_default_risk_config()
                )
                
                # Validate and update fields
                for field, value in config_data.items():
                    if hasattr(config, field):
                        # Convert string values to Decimal for numeric fields
                        if field in ['max_position_size_usd', 'max_daily_loss_usd', 'max_daily_volume']:
                            value = Decimal(str(value))
                        setattr(config, field, value)
                
                config.save()
                
                # Clear cache using specific keys
                cache_keys_to_clear = [
                    f"risk_overview_{user.id}",
                    f"limits_utilization_{user.id}",
                    f"risk_alerts_{user.id}",
                    f"risk_dashboard_{user.id}",
                    f"integrated_config_{user.id}",
                ]
                
                for key in cache_keys_to_clear:
                    try:
                        cache.delete(key)
                    except Exception as e:
                        logger.warning(f"Failed to delete cache key {key}: {e}")
                
                logger.info("Updated risk config for user %s", user.id)
                return True, "Risk configuration updated successfully"
                
        except Exception as exc:
            logger.exception("Error updating risk config for user %s: %s", user.id, exc)
            return False, f"Failed to update risk configuration: {str(exc)}"

    @staticmethod
    def _get_default_risk_config() -> Dict[str, Any]:
        """Default risk configuration"""
        return {
            'max_position_size_usd': Decimal('5000.00'),
            'max_trades_per_day': 50,
            'max_daily_loss_usd': Decimal('500.00'),
            'max_daily_volume': Decimal('25000.00'),
            'risk_tolerance': 'medium'
        }

    @staticmethod
    def update_risk_metrics(user, trade_data: Dict[str, Any], pnl: Optional[Decimal] = None) -> None:
        """
        Update risk metrics after a trade - for integration with trading services
        """
        try:
            LimitMonitoringService.update_trade_metrics(user, trade_data, pnl)
            
            # Clear relevant caches using specific keys
            cache_keys_to_clear = [
                f"risk_overview_{user.id}",
                f"limits_utilization_{user.id}",
                f"risk_alerts_{user.id}",
                f"risk_dashboard_{user.id}",
                f"user_trading_stats_{user.id}_30",
                f"user_trading_stats_{user.id}_7",
                f"user_trading_stats_{user.id}_90",
                f"integrated_dashboard_{user.id}",
                f"integrated_stats_{user.id}_30",
                f"integrated_stats_{user.id}_7",
                f"integrated_stats_{user.id}_90",
            ]
            
            for key in cache_keys_to_clear:
                try:
                    cache.delete(key)
                except Exception as e:
                    logger.warning(f"Failed to delete cache key {key}: {e}")
            
        except Exception as exc:
            logger.error("Error updating risk metrics for user %s: %s", user.id, exc)


class LimitMonitoringService:
    """
    Service for monitoring and managing trading limits
    """
    
    @staticmethod
    def reset_daily_limits():
        """Reset daily trading limits for all users"""
        from apps.users.models import User
        
        today = timezone.now().date()
        active_users = User.objects.filter(is_active=True)
        reset_count = 0
        
        for user in active_users:
            try:
                RiskMetrics.objects.update_or_create(
                    user=user,
                    date=today,
                    defaults={
                        'daily_trades': 0,
                        'daily_volume': Decimal('0.0'),
                        'daily_pnl': Decimal('0.0')
                    }
                )
                reset_count += 1
            except Exception as exc:
                logger.error("Error resetting limits for user %s: %s", user.id, exc)
        
        logger.info("Daily limits reset for %d active users", reset_count)
        return reset_count
    
    @staticmethod
    def check_user_limits(user, trade_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if user has reached any trading limits"""
        try:
            today = timezone.now().date()
            metrics, created = RiskMetrics.objects.get_or_create(
                user=user,
                date=today,
                defaults={
                    'daily_trades': 0,
                    'daily_volume': Decimal('0.0'),
                    'daily_pnl': Decimal('0.0')
                }
            )
            
            risk_config = RiskConfig.objects.filter(user=user).first()
            if not risk_config:
                return False, "No risk configuration found"
            
            # Check daily trade limit
            if metrics.daily_trades >= risk_config.max_trades_per_day:
                return False, f"Daily trade limit reached ({metrics.daily_trades}/{risk_config.max_trades_per_day})"
            
            # Check daily volume limit
            trade_amount = Decimal(str(trade_data.get('amount', 0)))
            trade_price = Decimal(str(trade_data.get('price', 1)))
            trade_volume = trade_amount * trade_price
            
            if (metrics.daily_volume + trade_volume) > risk_config.max_daily_volume:
                remaining = risk_config.max_daily_volume - metrics.daily_volume
                return False, f"Daily volume limit exceeded. Remaining: ${remaining:.2f}"
            
            # Check position size limit
            if trade_volume > risk_config.max_position_size_usd:
                return False, f"Position size ${trade_volume:.2f} exceeds maximum ${risk_config.max_position_size_usd:.2f}"
            
            return True, "Within limits"
            
        except Exception as exc:
            logger.error("Error checking user limits for user %s: %s", getattr(user, "id", None), exc)
            return False, "Error checking limits"
    
    @staticmethod
    def update_trade_metrics(user, trade_data: Dict[str, Any], pnl: Optional[Decimal] = None):
        """
        Update user trade metrics after a successful trade
        """
        try:
            with transaction.atomic():
                today = timezone.now().date()
                metrics, created = RiskMetrics.objects.get_or_create(
                    user=user,
                    date=today,
                    defaults={
                        'daily_trades': 0,
                        'daily_volume': Decimal('0.0'),
                        'daily_pnl': Decimal('0.0')
                    }
                )
                
                # Update trade count
                metrics.daily_trades += 1
                
                # Update volume
                trade_amount = Decimal(str(trade_data.get('amount', 0)))
                trade_price = Decimal(str(trade_data.get('price', 1)))
                trade_volume = trade_amount * trade_price
                metrics.daily_volume += trade_volume
                
                # Update PnL if provided
                if pnl is not None:
                    metrics.daily_pnl += Decimal(str(pnl))
                
                metrics.save()
                logger.info("Updated trade metrics for user %s: trades=%d, volume=%.2f", 
                           user.id, metrics.daily_trades, float(metrics.daily_volume))
                
        except Exception as exc:
            logger.error("Error updating trade metrics for user %s: %s", user.id, exc)
            raise
    
    @staticmethod
    def get_user_daily_metrics(user) -> Dict[str, Any]:
        """
        Get user's daily trading metrics
        """
        try:
            today = timezone.now().date()
            metrics = RiskMetrics.objects.filter(user=user, date=today).first()
            
            if not metrics:
                return {
                    'daily_trades': 0,
                    'daily_volume': Decimal('0.0'),
                    'daily_pnl': Decimal('0.0')
                }
            
            return {
                'daily_trades': metrics.daily_trades,
                'daily_volume': metrics.daily_volume,
                'daily_pnl': metrics.daily_pnl
            }
            
        except Exception as exc:
            logger.error("Error getting user daily metrics for user %s: %s", getattr(user, "id", None), exc)
            return {
                'daily_trades': 0,
                'daily_volume': Decimal('0.0'),
                'daily_pnl': Decimal('0.0')
            }
    
    @staticmethod
    def check_and_enforce_limits(user, trade_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Comprehensive limit check and enforcement
        """
        # Check basic limits
        within_limits, message = LimitMonitoringService.check_user_limits(user, trade_data)
        if not within_limits:
            return False, message
        
        # Check risk compliance
        compliant, risk_message = RiskManagementService.check_trade_compliance(user, trade_data)
        if not compliant:
            return False, risk_message
        
        return True, "All limits and compliance checks passed"
    
    @staticmethod
    def get_limits_utilization(user) -> Dict[str, Any]:
        """
        Get current utilization of all trading limits
        """
        cache_key = f"limits_utilization_{user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        try:
            risk_config = RiskConfig.objects.filter(user=user).first()
            if not risk_config:
                return {"error": "No risk configuration found"}
            
            metrics = LimitMonitoringService.get_user_daily_metrics(user)
            
            utilization_data = {
                "daily_trades": {
                    "current": metrics['daily_trades'],
                    "limit": risk_config.max_trades_per_day,
                    "utilization": min(100, (metrics['daily_trades'] / risk_config.max_trades_per_day) * 100) if risk_config.max_trades_per_day > 0 else 0,
                    "remaining": max(0, risk_config.max_trades_per_day - metrics['daily_trades'])
                },
                "daily_volume": {
                    "current": float(metrics['daily_volume']),
                    "limit": float(risk_config.max_daily_volume),
                    "utilization": min(100, (float(metrics['daily_volume']) / float(risk_config.max_daily_volume)) * 100) if risk_config.max_daily_volume > 0 else 0,
                    "remaining": float(max(Decimal('0'), risk_config.max_daily_volume - metrics['daily_volume']))
                },
                "position_size": {
                    "limit": float(risk_config.max_position_size_usd)
                },
                "daily_loss": {
                    "current": float(metrics['daily_pnl']),
                    "limit": float(risk_config.max_daily_loss_usd),
                    "utilization": min(100, (abs(float(metrics['daily_pnl'])) / float(risk_config.max_daily_loss_usd)) * 100) if risk_config.max_daily_loss_usd > 0 and metrics['daily_pnl'] < 0 else 0
                },
                "timestamp": timezone.now().isoformat()
            }
            
            # Cache for 2 minutes
            cache.set(cache_key, utilization_data, 120)
            return utilization_data
            
        except Exception as exc:
            logger.error("Error getting limits utilization for user %s: %s", getattr(user, "id", None), exc)
            return {"error": "Failed to calculate limits utilization"}


class RiskAlertService:
    """
    Service for generating and managing risk alerts
    """
    
    @staticmethod
    def check_for_risk_alerts(user) -> List[Dict[str, Any]]:
        """
        Check for potential risk alerts for a user
        """
        cache_key = f"risk_alerts_{user.id}"
        cached_alerts = cache.get(cache_key)
        
        if cached_alerts:
            return cached_alerts
            
        alerts = []
        
        try:
            risk_config = RiskConfig.objects.filter(user=user).first()
            if not risk_config:
                return alerts
            
            metrics = LimitMonitoringService.get_user_daily_metrics(user)
            utilization = LimitMonitoringService.get_limits_utilization(user)
            
            # High utilization alerts
            if utilization.get('daily_trades', {}).get('utilization', 0) > 80:
                alerts.append({
                    'type': 'WARNING',
                    'severity': 'medium',
                    'message': 'Daily trade limit utilization high',
                    'details': f"Used {utilization['daily_trades']['current']}/{utilization['daily_trades']['limit']} trades",
                    'code': 'HIGH_TRADE_UTILIZATION'
                })
            
            if utilization.get('daily_volume', {}).get('utilization', 0) > 80:
                alerts.append({
                    'type': 'WARNING',
                    'severity': 'medium',
                    'message': 'Daily volume limit utilization high',
                    'details': f"Used ${utilization['daily_volume']['current']:.2f}/${utilization['daily_volume']['limit']:.2f}",
                    'code': 'HIGH_VOLUME_UTILIZATION'
                })
            
            # Negative PnL alert
            if metrics['daily_pnl'] < Decimal('-100.00'):
                alerts.append({
                    'type': 'ALERT',
                    'severity': 'high',
                    'message': 'Significant daily loss',
                    'details': f"Daily PnL: ${float(metrics['daily_pnl']):.2f}",
                    'code': 'SIGNIFICANT_LOSS'
                })
            
            # Approaching daily loss limit
            if utilization.get('daily_loss', {}).get('utilization', 0) > 70:
                alerts.append({
                    'type': 'WARNING',
                    'severity': 'medium',
                    'message': 'Approaching daily loss limit',
                    'details': f"Current loss: ${abs(float(metrics['daily_pnl'])):.2f}, Limit: ${risk_config.max_daily_loss_usd:.2f}",
                    'code': 'APPROACHING_LOSS_LIMIT'
                })
            
            # High trade frequency alert
            if metrics['daily_trades'] > risk_config.max_trades_per_day * 0.7:
                alerts.append({
                    'type': 'INFO',
                    'severity': 'low',
                    'message': 'High trading frequency',
                    'details': f"Completed {metrics['daily_trades']} trades today",
                    'code': 'HIGH_TRADE_FREQUENCY'
                })
            
            # Cache alerts for 5 minutes
            cache.set(cache_key, alerts, 300)
            return alerts
            
        except Exception as exc:
            logger.error("Error checking risk alerts for user %s: %s", getattr(user, "id", None), exc)
            return alerts
    
    @staticmethod
    def get_risk_alerts(user) -> List[Dict[str, Any]]:
        """
        Get active risk alerts for user (alias for check_for_risk_alerts for compatibility)
        """
        return RiskAlertService.check_for_risk_alerts(user)
    
    @staticmethod
    def clear_risk_alerts_cache(user) -> None:
        """
        Clear cached risk alerts for user
        """
        cache_key = f"risk_alerts_{user.id}"
        try:
            cache.delete(cache_key)
        except Exception as e:
            logger.warning(f"Failed to delete cache key {cache_key}: {e}")


# Export commonly used functions for easy access
def validate_trade_with_risk(user, trade_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate trade with risk management system.
    
    Args:
        user: User making the trade
        trade_data: Trade data to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    return RiskManagementService.check_trade_compliance(user, trade_data)


def get_risk_dashboard_data(user) -> Dict[str, Any]:
    """
    Get comprehensive risk dashboard data for user
    
    Returns:
        Dict: Combined risk overview, limits utilization, and alerts
    """
    cache_key = f"risk_dashboard_{user.id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
        
    try:
        risk_overview = RiskManagementService.get_user_risk_overview(user)
        limits_utilization = LimitMonitoringService.get_limits_utilization(user)
        risk_alerts = RiskAlertService.get_risk_alerts(user)
        
        dashboard_data = {
            'risk_overview': risk_overview,
            'limits_utilization': limits_utilization,
            'risk_alerts': risk_alerts,
            'timestamp': timezone.now().isoformat()
        }
        
        # Cache for 2 minutes
        cache.set(cache_key, dashboard_data, 120)
        return dashboard_data
        
    except Exception as exc:
        logger.error("Error getting risk dashboard data for user %s: %s", user.id, exc)
        return {
            'risk_overview': {},
            'limits_utilization': {},
            'risk_alerts': [],
            'error': 'Failed to load risk dashboard data'
        }


def clear_risk_caches(user) -> None:
    """
    Clear all risk-related caches for user
    """
    cache_keys = [
        f"risk_overview_{user.id}",
        f"limits_utilization_{user.id}",
        f"risk_alerts_{user.id}",
        f"risk_dashboard_{user.id}"
    ]
    
    for key in cache_keys:
        try:
            cache.delete(key)
        except Exception as e:
            logger.warning(f"Failed to delete cache key {key}: {e}")


# Safe cache utility functions
def safe_cache_delete_keys(keys: list) -> None:
    """
    Safely delete specific cache keys.
    """
    for key in keys:
        try:
            cache.delete(key)
        except Exception as e:
            logger.warning(f"Failed to delete cache key {key}: {e}")


def get_cache_backend_info() -> dict:
    """
    Get information about the current cache backend.
    """
    backend = getattr(cache, 'backend', None)
    return {
        'backend_class': str(type(backend)) if backend else 'Unknown',
        'supports_patterns': hasattr(cache, 'delete_pattern'),
        'supports_clear': hasattr(cache, 'clear') if backend else False,
    }