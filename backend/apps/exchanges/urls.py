# backend/apps/exchanges/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_integration import UserExchangeIntegrationViewSet, ExchangeConnectorViewSet

router = DefaultRouter()
router.register(r'exchanges', views.ExchangeViewSet, basename='exchanges')
router.register(r'market-data', views.MarketDataViewSet, basename='market-data')
router.register(r'credentials', views.ExchangeCredentialsViewSet, basename='credentials')
router.register(r'operations', views.ExchangeOperationsViewSet, basename='operations')

urlpatterns = [
    path('', include(router.urls)),
    
    # Frontend-compatible endpoints for settings
    path('configured/', views.ExchangeViewSet.as_view({'get': 'user_exchange_settings'}), 
         name='exchange-configured'),
    path('settings/', views.ExchangeViewSet.as_view({'put': 'update_user_settings'}), 
         name='exchange-settings'),
    
    # Additional exchange operations endpoints
    path('operations/balances/', views.ExchangeOperationsViewSet.as_view({'get': 'balances'}), 
         name='exchange-balances'),
    path('operations/connectivity/', views.ExchangeOperationsViewSet.as_view({'get': 'test_connectivity'}), 
         name='exchange-connectivity'),
    path('operations/sync-market-data/', views.ExchangeOperationsViewSet.as_view({'post': 'sync_market_data'}), 
         name='sync-market-data'),
    path('operations/status/', views.ExchangeOperationsViewSet.as_view({'get': 'exchange_status'}), 
         name='exchange-status'),
    
    # API Key validation endpoint
    path('validate-api-key/', views.ExchangeCredentialsViewSet.as_view({'post': 'validate'}), 
         name='validate-api-key'),
    
    # Legacy endpoints for backward compatibility
    path('user-settings/', views.ExchangeViewSet.as_view({'get': 'user_settings'}), 
         name='exchange-user-settings'),
    path('legacy-settings/', views.ExchangeViewSet.as_view({'put': 'update_settings'}), 
         name='exchange-legacy-settings'),

     # Test exchange settings endpoint
     path('test-settings/', views.ExchangeViewSet.as_view({'post': 'test_settings'}), 
     name='test-settings'),

    # User exchange integration endpoints
    path('user-exchanges/', UserExchangeIntegrationViewSet.as_view({'get': 'my_exchanges'}), 
         name='user-exchanges'),
    path('user-exchanges/balances/', UserExchangeIntegrationViewSet.as_view({'get': 'balances'}), 
         name='user-exchanges-balances'),
    path('user-exchanges/connection-status/', UserExchangeIntegrationViewSet.as_view({'get': 'connection_status'}), 
         name='user-exchanges-connection-status'),
    path('user-exchanges/<int:pk>/test-connection/', UserExchangeIntegrationViewSet.as_view({'get': 'test_connection'}), 
         name='user-exchange-test-connection'),
    path('user-exchanges/<int:pk>/balance/', UserExchangeIntegrationViewSet.as_view({'get': 'balance'}), 
         name='user-exchange-balance'),
    
    # Exchange connector endpoints
    path('connectors/create/', ExchangeConnectorViewSet.as_view({'post': 'create_connector'}), 
         name='exchange-connector-create'),
]

# Add namespace for reverse URL lookups
app_name = 'exchanges'