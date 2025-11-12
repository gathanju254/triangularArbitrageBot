# backend/apps/risk_management/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'config', views.RiskConfigViewSet, basename='risk-config')
router.register(r'metrics', views.RiskMetricsViewSet, basename='risk-metrics')
router.register(r'limits', views.TradeLimitViewSet, basename='trade-limits')

urlpatterns = [
    path('', include(router.urls)),
    
    # Additional endpoints
    path('overview/', views.RiskOverviewView.as_view(), name='risk-overview'),
    path('check-trade/', views.check_trade_compliance, name='check-trade-compliance'),
    
    # Backward compatibility - keep the old endpoint names
    path('metrics/list/', views.RiskMetricsView.as_view(), name='risk-metrics-list'),
]