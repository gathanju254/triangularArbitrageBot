# backend/apps/risk_management/views_dashboard.py
# backend/apps/risk_management/views_dashboard.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Avg
from .models import RiskConfig, RiskMetrics, TradeLimit

class RiskDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        today = timezone.now().date()
        
        # Risk configuration
        risk_config = RiskConfig.objects.filter(user=user).first()
        
        # Current risk metrics
        today_metrics = RiskMetrics.objects.filter(user=user, date=today).first()
        
        # Limit breaches
        active_limits = TradeLimit.objects.filter(user=user)
        breached_limits = active_limits.filter(is_breached=True)
        
        # Historical risk data
        risk_history = RiskMetrics.objects.filter(
            user=user,
            date__gte=today - timedelta(days=30)
        ).order_by('date')
        
        stats = {
            'risk_config': {
                'max_position_size': risk_config.max_position_size_usd if risk_config else 0,
                'max_trades_per_day': risk_config.max_trades_per_day if risk_config else 0,
                'max_daily_volume': risk_config.max_daily_volume if risk_config else 0,
                'risk_tolerance': risk_config.risk_tolerance if risk_config else 'medium'
            },
            'current_metrics': {
                'daily_trades': today_metrics.daily_trades if today_metrics else 0,
                'daily_volume': today_metrics.daily_volume if today_metrics else 0,
                'daily_pnl': today_metrics.daily_pnl if today_metrics else 0,
                'sharpe_ratio': today_metrics.sharpe_ratio if today_metrics else 0,
                'volatility': today_metrics.volatility if today_metrics else 0,
                'max_drawdown': today_metrics.max_drawdown if today_metrics else 0
            },
            'limit_monitoring': {
                'active_limits': active_limits.count(),
                'breached_limits': breached_limits.count(),
                'breach_alerts': breached_limits.values('limit_type', 'limit_value', 'current_value')
            },
            'risk_score': {
                'current_score': today_metrics.risk_score if today_metrics else 0,
                'trend_30d': self._calculate_risk_trend(risk_history),
                'recommendations': self._generate_risk_recommendations(user)
            }
        }
        
        return Response(stats)
    
    def _calculate_risk_trend(self, risk_history):
        # Calculate risk trend over 30 days
        if risk_history.count() < 2:
            return 'stable'
        
        first_score = risk_history.first().risk_score or 0
        last_score = risk_history.last().risk_score or 0
        
        if last_score > first_score + 0.1:
            return 'increasing'
        elif last_score < first_score - 0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _generate_risk_recommendations(self, user):
        # Generate risk management recommendations
        recommendations = []
        
        # Example recommendations
        today_metrics = RiskMetrics.objects.filter(user=user, date=timezone.now().date()).first()
        if today_metrics and today_metrics.daily_trades > 50:
            recommendations.append("Consider reducing trade frequency to manage risk")
        
        risk_config = RiskConfig.objects.filter(user=user).first()
        if risk_config and risk_config.risk_tolerance == 'high':
            recommendations.append("High risk tolerance detected - consider reviewing position sizes")
        
        return recommendations