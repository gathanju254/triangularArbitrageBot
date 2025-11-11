# backend/apps/trading/apps.py
from django.apps import AppConfig

class TradingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.trading'

    def ready(self):
        import apps.trading.signals