# backend/apps/arbitrage_bot/views/performance_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
import logging
import time
from django.utils import timezone
from datetime import timedelta
from django.db import models
from ..core.market_data import market_data_manager
from ..core.arbitrage_engine import arbitrage_engine
from ..core.order_execution import OrderExecutor
from ..models.trade import TradeRecord

logger = logging.getLogger(__name__)

market_data_manager_instance = market_data_manager
arbitrage_engine_instance = arbitrage_engine
order_executor = OrderExecutor()

@api_view(['GET'])
def get_performance(request):
    """Get performance metrics (real data from RiskManager + DB)"""
    try:
        # runtime components / models
        market_stats = market_data_manager_instance.get_price_statistics()
        engine_stats = arbitrage_engine_instance.get_triangle_statistics()

        # risk manager metrics
        rm = getattr(order_executor, 'risk_manager', None)
        risk_metrics = rm.get_risk_metrics() if (rm and callable(getattr(rm, 'get_risk_metrics', None))) else {}

        # execution stats
        exec_stats = getattr(order_executor, 'get_execution_stats', lambda: {})()

        # derive time-windowed stats from DB
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)

        total_profit_db = 0.0
        trades_today = 0
        weekly_profit = 0.0
        try:
            trades_qs = TradeRecord.objects.all()
            total_profit_db = float(trades_qs.aggregate(total=models.Sum('profit'))['total'] or 0.0)
            trades_today = trades_qs.filter(timestamp__gte=today_start).count()
            weekly_profit = float(trades_qs.filter(timestamp__gte=week_start).aggregate(total=models.Sum('profit'))['total'] or 0.0)
        except Exception as e:
            logger.debug(f"No DB trade stats available: {e}")

        # active opportunities (quick scan)
        try:
            current_prices = market_data_manager_instance.get_all_prices()
            price_values = {}
            for symbol, price_data in current_prices.items():
                if isinstance(price_data, dict) and 'price' in price_data:
                    price_values[symbol] = price_data['price']
                else:
                    price_values[symbol] = price_data
            active_opps = arbitrage_engine_instance.scan_opportunities(price_values)
            active_count = len(active_opps)
        except Exception:
            active_count = 0

        response = {
            'totalProfit': round(total_profit_db, 2),
            'tradesToday': trades_today,
            'activeOpportunities': active_count,
            'successRate': risk_metrics.get('success_rate', exec_stats.get('success_rate', 0.0)),
            'dailyProfit': round(risk_metrics.get('daily_pnl', 0.0), 2),
            'weeklyProfit': round(weekly_profit, 2),
            'monthlyProfit': round(total_profit_db, 2),
            'market_coverage': market_stats.get('total_symbols', 0),
            'triangle_efficiency': min(100, (engine_stats.get('total_triangles', 0) / max(1, market_stats.get('total_symbols', 1))) * 100),
            'risk_metrics': risk_metrics,
            'execution_stats': exec_stats,
            'timestamp': time.time()
        }

        return Response(response)

    except Exception as e:
        logger.error(f"Error generating performance metrics: {e}")
        return Response({
            'totalProfit': 0.0,
            'tradesToday': 0,
            'activeOpportunities': 0,
            'successRate': 0.0,
            'dailyProfit': 0.0,
            'weeklyProfit': 0.0,
            'monthlyProfit': 0.0,
            'market_coverage': 0,
            'triangle_efficiency': 0,
            'note': 'Using fallback performance data',
            'timestamp': time.time()
        })

@api_view(['GET'])
def get_performance_alias(request):
    """Get performance metrics - alias for api_views.get_performance"""
    from .api_views import get_performance as api_get_performance
    return api_get_performance(request)