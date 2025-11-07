# backend/arbitrage_bot/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('system/status/', views.system_status, name='system_status'),
    path('system/control/', views.system_control, name='system_control'),
    path('opportunities/', views.get_opportunities, name='get_opportunities'),
    path('performance/', views.get_performance, name='get_performance'),
    path('trading/execute/', views.execute_trade, name='execute_trade'),
    path('trading/history/', views.get_trade_history, name='get_trade_history'),
    path('settings/', views.get_settings, name='get_settings'),
    path('settings/update/', views.update_settings, name='update_settings'),
    path('health/', views.health_check, name='health_check'),  # Added health endpoint

    # Real trading endpoints
    path('trading/enable_real/', views.enable_real_trading, name='enable_real_trading'),
    path('trading/disable_real/', views.disable_real_trading, name='disable_real_trading'),
    path('risk/metrics/', views.get_risk_metrics, name='get_risk_metrics'),
    path('risk/update_limits/', views.update_risk_limits, name='update_risk_limits'),

    path('trading/monitor/start/', views.start_trading_monitor, name='start_trading_monitor'),
    path('trading/monitor/stop/', views.stop_trading_monitor, name='stop_trading_monitor'),
    path('trading/monitor/status/', views.get_trading_monitor_status, name='get_trading_monitor_status'),
]