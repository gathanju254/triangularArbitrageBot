# backend/apps/risk_management/engines/risk_calculator.py
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from typing import List, Optional
from django.db.models import Max, Avg


class RiskCalculator:
    """Calculate portfolio risk with proper decimal handling and comprehensive risk metrics"""
    
    def calculate_portfolio_risk(self, user) -> Decimal:
        """Calculate overall portfolio risk score (0-100) with proper decimal handling"""
        try:
            risk_factors = [
                self._calculate_drawdown_risk(user),
                self._calculate_concentration_risk(user),
                self._calculate_liquidity_risk(user),
                self._calculate_volatility_risk(user),
                self._calculate_leverage_risk(user),
                self._calculate_market_risk(user)
            ]
            
            # Weighted average of risk factors with proper decimal conversion
            weights = [0.25, 0.20, 0.15, 0.20, 0.10, 0.10]  # Drawdown and volatility have highest weights
            decimal_weights = [Decimal(str(weight)) for weight in weights]
            
            # Calculate total risk with proper decimal arithmetic
            total_risk = Decimal('0.0')
            for factor, weight in zip(risk_factors, decimal_weights):
                total_risk += factor * weight
            
            return min(total_risk, Decimal('100.00'))
            
        except Exception as e:
            print(f"Error calculating portfolio risk: {e}")
            return Decimal('25.0')  # Default medium risk on error

    def calculate_var(self, user, confidence_level: float = 0.95, time_horizon: int = 1) -> Decimal:
        """Calculate Value at Risk with proper decimal handling"""
        try:
            portfolio_value = self._get_portfolio_value(user)
            volatility = self._calculate_historical_volatility(user)
            
            # Simplified VaR calculation with decimal conversion
            z_score = self._get_z_score(confidence_level)
            time_factor = Decimal(str(time_horizon ** 0.5))
            
            var = portfolio_value * z_score * volatility * time_factor
            
            return max(var, Decimal('0.00'))  # VaR should be non-negative
            
        except Exception as e:
            print(f"Error calculating VaR: {e}")
            return Decimal('0.00')

    def calculate_expected_shortfall(self, user, confidence_level: float = 0.95) -> Decimal:
        """Calculate Expected Shortfall (CVaR) with proper decimal handling"""
        try:
            var = self.calculate_var(user, confidence_level)
            # ES is typically 1.5-2 times VaR for normal distributions
            es_multiplier = Decimal('1.75')
            return var * es_multiplier
            
        except Exception as e:
            print(f"Error calculating Expected Shortfall: {e}")
            return Decimal('0.00')

    def calculate_risk_metrics(self, user) -> dict:
        """Calculate comprehensive risk metrics for user"""
        return {
            'portfolio_risk_score': float(self.calculate_portfolio_risk(user)),
            'var_95': float(self.calculate_var(user, 0.95)),
            'var_99': float(self.calculate_var(user, 0.99)),
            'expected_shortfall_95': float(self.calculate_expected_shortfall(user, 0.95)),
            'drawdown_risk': float(self._calculate_drawdown_risk(user)),
            'concentration_risk': float(self._calculate_concentration_risk(user)),
            'liquidity_risk': float(self._calculate_liquidity_risk(user)),
            'volatility_risk': float(self._calculate_volatility_risk(user)),
            'leverage_risk': float(self._calculate_leverage_risk(user)),
            'market_risk': float(self._calculate_market_risk(user))
        }

    def _calculate_drawdown_risk(self, user) -> Decimal:
        """Calculate risk from maximum drawdown with proper error handling"""
        from ..models import RiskMetrics
        
        try:
            # Get the maximum drawdown from user's risk metrics
            max_drawdown_result = RiskMetrics.objects.filter(
                user=user
            ).aggregate(max_dd=Max('max_drawdown'))
            
            max_drawdown = max_drawdown_result.get('max_dd')
            
            if max_drawdown:
                # Convert drawdown percentage to risk score (0-100)
                # 10% drawdown = 20 risk points, 50% drawdown = 100 risk points
                risk_score = max_drawdown * Decimal('2.0')
                return min(risk_score, Decimal('100.00'))
                
        except Exception as e:
            print(f"Error calculating drawdown risk: {e}")
            
        return Decimal('15.0')  # Default medium risk

    def _calculate_concentration_risk(self, user) -> Decimal:
        """Calculate concentration risk based on position distribution"""
        try:
            from apps.trading.models import Order
            
            # Get recent trades to analyze concentration
            recent_orders = Order.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(days=30)
            )
            
            if not recent_orders.exists():
                return Decimal('10.0')  # Low risk if no trades
                
            # Analyze symbol concentration
            symbol_counts = {}
            total_trades = recent_orders.count()
            
            for order in recent_orders:
                symbol = order.symbol
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            # Calculate Herfindahl index for concentration
            herfindahl = Decimal('0.0')
            for count in symbol_counts.values():
                market_share = Decimal(str(count)) / Decimal(str(total_trades))
                herfindahl += market_share * market_share
            
            # Convert to risk score (0-100)
            # HHI of 0.1 = 10 risk points, HHI of 1.0 = 100 risk points
            concentration_risk = herfindahl * Decimal('100.0')
            return min(concentration_risk, Decimal('100.00'))
            
        except Exception as e:
            print(f"Error calculating concentration risk: {e}")
            return Decimal('15.0')  # Default medium risk

    def _calculate_liquidity_risk(self, user) -> Decimal:
        """Calculate liquidity risk based on trading patterns"""
        try:
            from apps.trading.models import Order
            
            # Analyze trade frequency and size for liquidity assessment
            recent_orders = Order.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(days=7)
            )
            
            if not recent_orders.exists():
                return Decimal('5.0')  # Low risk if no recent trading
                
            total_volume = sum(float(order.amount) for order in recent_orders)
            avg_trade_size = total_volume / len(recent_orders)
            
            # Higher average trade size indicates higher liquidity risk
            if avg_trade_size > 10000:  # $10k+ average trade size
                return Decimal('30.0')
            elif avg_trade_size > 5000:  # $5k-10k average trade size
                return Decimal('20.0')
            elif avg_trade_size > 1000:  # $1k-5k average trade size
                return Decimal('15.0')
            else:  # < $1k average trade size
                return Decimal('8.0')
                
        except Exception as e:
            print(f"Error calculating liquidity risk: {e}")
            return Decimal('10.0')  # Default medium risk

    def _calculate_volatility_risk(self, user) -> Decimal:
        """Calculate volatility risk based on historical volatility"""
        from ..models import RiskMetrics
        
        try:
            recent_metrics = RiskMetrics.objects.filter(
                user=user,
                date__gte=timezone.now().date() - timedelta(days=30)
            )
            
            if recent_metrics.exists():
                # Calculate average volatility
                avg_volatility = recent_metrics.aggregate(
                    avg_vol=Avg('volatility')
                )['avg_vol'] or Decimal('0.02')  # Default 2% volatility
                
                # Convert volatility to risk score
                # 2% volatility = 20 risk points, 10% volatility = 100 risk points
                volatility_risk = avg_volatility * Decimal('500.0')  # Scale factor
                return min(volatility_risk, Decimal('100.00'))
                
        except Exception as e:
            print(f"Error calculating volatility risk: {e}")
            
        return Decimal('20.0')  # Default medium-high risk

    def _calculate_leverage_risk(self, user) -> Decimal:
        """Calculate leverage risk based on trading behavior"""
        try:
            from apps.trading.models import Order
            from ..models import RiskConfig
            
            # Get user's risk configuration
            risk_config = RiskConfig.objects.filter(user=user).first()
            if not risk_config:
                return Decimal('15.0')
                
            # Analyze recent trading volume vs limits
            daily_metrics = self._get_user_daily_metrics(user)
            max_daily_volume = risk_config.max_daily_volume
            current_volume = daily_metrics.get('daily_volume', Decimal('0.0'))
            
            if max_daily_volume > 0:
                utilization = current_volume / max_daily_volume
                # High utilization indicates higher leverage risk
                if utilization > Decimal('0.8'):
                    return Decimal('40.0')
                elif utilization > Decimal('0.5'):
                    return Decimal('25.0')
                elif utilization > Decimal('0.2'):
                    return Decimal('15.0')
                else:
                    return Decimal('8.0')
                    
        except Exception as e:
            print(f"Error calculating leverage risk: {e}")
            
        return Decimal('15.0')  # Default medium risk

    def _calculate_market_risk(self, user) -> Decimal:
        """Calculate general market risk based on portfolio composition"""
        try:
            from apps.trading.models import Order
            
            # Analyze portfolio exposure to different markets
            recent_orders = Order.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(days=30)
            )
            
            crypto_exposure = recent_orders.filter(
                symbol__contains='/USDT'
            ).count()
            
            total_orders = recent_orders.count()
            
            if total_orders > 0:
                crypto_ratio = Decimal(str(crypto_exposure)) / Decimal(str(total_orders))
                # Higher crypto exposure = higher market risk
                market_risk = crypto_ratio * Decimal('60.0') + Decimal('10.0')  # Base 10 + crypto risk
                return min(market_risk, Decimal('100.00'))
                
        except Exception as e:
            print(f"Error calculating market risk: {e}")
            
        return Decimal('25.0')  # Default medium-high risk for crypto

    def _get_portfolio_value(self, user) -> Decimal:
        """Get user's portfolio value with proper decimal handling"""
        try:
            # This would integrate with your portfolio service
            # For now, return a default value
            return Decimal('10000.00')
        except Exception as e:
            print(f"Error getting portfolio value: {e}")
            return Decimal('5000.00')  # Default portfolio value

    def _calculate_historical_volatility(self, user) -> Decimal:
        """Calculate historical portfolio volatility"""
        try:
            from ..models import RiskMetrics
            
            recent_metrics = RiskMetrics.objects.filter(
                user=user,
                date__gte=timezone.now().date() - timedelta(days=30)
            )
            
            if recent_metrics.exists():
                avg_volatility = recent_metrics.aggregate(
                    avg_vol=Avg('volatility')
                )['avg_vol']
                return avg_volatility or Decimal('0.02')
                
        except Exception as e:
            print(f"Error calculating historical volatility: {e}")
            
        return Decimal('0.02')  # Default 2% daily volatility

    def _get_z_score(self, confidence_level: float) -> Decimal:
        """Get Z-score for given confidence level with decimal conversion"""
        z_scores = {
            0.90: Decimal('1.282'),
            0.95: Decimal('1.645'),
            0.99: Decimal('2.326'),
            0.995: Decimal('2.576')
        }
        return z_scores.get(confidence_level, Decimal('1.645'))

    def _get_user_daily_metrics(self, user) -> dict:
        """Get user's daily trading metrics"""
        from ..models import RiskMetrics
        
        try:
            today = timezone.now().date()
            metrics = RiskMetrics.objects.filter(user=user, date=today).first()
            
            if metrics:
                return {
                    'daily_trades': metrics.daily_trades,
                    'daily_volume': metrics.daily_volume,
                    'daily_pnl': metrics.daily_pnl
                }
        except Exception as e:
            print(f"Error getting user daily metrics: {e}")
            
        return {
            'daily_trades': 0,
            'daily_volume': Decimal('0.0'),
            'daily_pnl': Decimal('0.0')
        }

    # Backward compatibility methods
    def _get_risk_factors(self, user) -> List[Decimal]:
        """Get risk factors for user (compatibility method)"""
        return [
            self._calculate_market_risk(user),
            self._calculate_liquidity_risk(user),
            self._calculate_concentration_risk(user),
            self._calculate_leverage_risk(user)
        ]
    
    def _get_risk_weights(self) -> List[float]:
        """Get risk weights (compatibility method)"""
        return [0.4, 0.2, 0.3, 0.1]