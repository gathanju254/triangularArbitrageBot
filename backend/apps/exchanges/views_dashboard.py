# backend/apps/exchanges/views_dashboard.py
# backend/apps/exchanges/views_dashboard.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg
from .models import Exchange, MarketData

class ExchangeDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Exchange connectivity and performance stats
        exchanges = Exchange.objects.all()
        
        exchange_stats = []
        for exchange in exchanges:
            recent_data = MarketData.objects.filter(
                exchange=exchange
            ).order_by('-timestamp')[:10]
            
            stats = {
                'name': exchange.name,
                'is_active': exchange.is_active,
                'last_update': exchange.last_update,
                'total_pairs': exchange.trading_pairs.count(),
                'recent_volume_24h': exchange.volume_24h or 0,
                'connectivity_status': exchange.get_connectivity_status(),
                'performance_metrics': {
                    'avg_response_time': exchange.avg_response_time or 0,
                    'success_rate': exchange.success_rate or 0,
                    'uptime_24h': exchange.uptime_24h or 0
                }
            }
            exchange_stats.append(stats)
        
        # Market overview
        top_volume_pairs = MarketData.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).values('symbol').annotate(
            total_volume=Avg('volume_24h'),
            avg_price=Avg('last_price')
        ).order_by('-total_volume')[:5]
        
        return Response({
            'exchange_stats': exchange_stats,
            'market_overview': {
                'top_volume_pairs': list(top_volume_pairs),
                'total_exchanges': exchanges.count(),
                'active_exchanges': exchanges.filter(is_active=True).count(),
                'total_trading_pairs': sum(exchange.trading_pairs.count() for exchange in exchanges)
            }
        })