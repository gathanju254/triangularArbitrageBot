# backend/arbitrage_bot/urls.py
from django.urls import path, include
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
]