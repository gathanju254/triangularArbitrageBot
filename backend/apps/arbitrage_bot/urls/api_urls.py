# backend/apps/arbitrage_bot/urls/api_urls.py
from django.urls import path
from ..views.api_views import (
    system_status,
    system_control,
    get_opportunities,
    health_check,
    reset_system,
    get_performance
)
from ..views.trading_views import (
    start_trading_monitor,
    stop_trading_monitor,
    get_trading_monitor_status,
    execute_trade,
    get_trade_history
)
from ..views.settings_views import (
    get_settings,
    update_settings,
    enable_real_trading,
    disable_real_trading,
    get_risk_metrics,
    update_risk_limits
)

urlpatterns = [
    # System endpoints
    path('system/status/', system_status, name='system_status'),
    path('system/control/', system_control, name='system_control'),
    path('system/health/', health_check, name='health_check'),
    path('system/reset/', reset_system, name='reset_system'),
    
    # Opportunities & Performance - ADD THESE MISSING ENDPOINTS
    path('opportunities/', get_opportunities, name='get_opportunities'),
    path('profit-history/', get_performance, name='profit_history'),  # Frontend expects this
    path('stats/', get_performance, name='get_stats'),  # For dashboard stats
    path('performance/', get_performance, name='get_performance'),
    
    # Trading endpoints
    path('trading/execute/', execute_trade, name='execute_trade'),
    path('trading/history/', get_trade_history, name='get_trade_history'),
    path('trading/monitor/start/', start_trading_monitor, name='start_trading_monitor'),
    path('trading/monitor/stop/', stop_trading_monitor, name='stop_trading_monitor'),
    path('trading/monitor/status/', get_trading_monitor_status, name='get_trading_monitor_status'),
    
    # Dashboard endpoints
    path('dashboard/overview/', get_opportunities, name='dashboard_overview'),  # Reuse opportunities for now
    
    # Settings & Risk Management
    path('settings/', get_settings, name='get_settings'),
    path('settings/update/', update_settings, name='update_settings'),
    path('trading/enable_real/', enable_real_trading, name='enable_real_trading'),
    path('trading/disable_real/', disable_real_trading, name='disable_real_trading'),
    path('risk/metrics/', get_risk_metrics, name='get_risk_metrics'),
    path('risk/update_limits/', update_risk_limits, name='update_risk_limits'),
]