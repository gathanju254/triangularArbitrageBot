# backend/apps/__init__.py
# Ensure all apps are properly connected
default_app_config = {
    'users': 'apps.users.apps.UsersConfig',
    'trading': 'apps.trading.apps.TradingConfig', 
    'arbitrage': 'apps.arbitrage.apps.ArbitrageConfig',
    'risk_management': 'apps.risk_management.apps.RiskManagementConfig',
    'exchanges': 'apps.exchanges.apps.ExchangesConfig',
    'notifications': 'apps.notifications.apps.NotificationsConfig',
    'analytics': 'apps.analytics.apps.AnalyticsConfig',
    #'exceptions': 'apps.exceptions.apps.ExceptionsConfig',
}