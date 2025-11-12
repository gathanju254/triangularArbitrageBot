# backend/apps/risk_management/engines/compliance_checker.py
from django.utils import timezone
from decimal import Decimal
from ..models import RiskConfig, TradeLimit

class ComplianceChecker:
    def __init__(self, risk_config):
        self.risk_config = risk_config

    def validate_trade(self, trade_data):
        """Validate trade against all risk limits"""
        checks = [
            self._check_position_size(trade_data),
            self._check_daily_loss_limit(trade_data),
            self._check_daily_trade_limit(),
            self._check_concurrent_trades(),
            self._check_circuit_breaker()
        ]

        for check_passed, message in checks:
            if not check_passed:
                return False, message

        return True, "Trade compliant with risk limits"

    def _check_position_size(self, trade_data):
        """Check if position size is within limits"""
        position_size = trade_data.get('position_size', Decimal('0'))
        max_position = self.risk_config.max_position_size_usd
        
        if position_size > max_position:
            return False, f"Position size {position_size} exceeds maximum {max_position}"
        
        return True, ""

    def _check_daily_loss_limit(self, trade_data):
        """Check daily loss limit"""
        try:
            loss_limit = TradeLimit.objects.get(
                user=self.risk_config.user,
                limit_type='daily_loss'
            )
            
            if loss_limit.is_breached:
                return False, "Daily loss limit breached"
                
        except TradeLimit.DoesNotExist:
            pass
            
        return True, ""

    def _check_daily_trade_limit(self):
        """Check daily trade count limit"""
        from ..models import RiskMetrics
        today = timezone.now().date()
        
        try:
            metrics = RiskMetrics.objects.get(
                user=self.risk_config.user,
                date=today
            )
            
            if metrics.daily_trades >= self.risk_config.max_trades_per_day:
                return False, "Daily trade limit reached"
                
        except RiskMetrics.DoesNotExist:
            pass
            
        return True, ""

    def _check_concurrent_trades(self):
        """Check concurrent trades limit"""
        # Implementation would check active trades count
        # This is a simplified version
        return True, ""

    def _check_circuit_breaker(self):
        """Check if circuit breaker is triggered"""
        from .circuit_breaker import CircuitBreaker
        circuit_breaker = CircuitBreaker()
        
        if circuit_breaker.is_triggered(self.risk_config.user):
            return False, "Circuit breaker active"
            
        return True, ""