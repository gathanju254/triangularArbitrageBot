# arbitrage_bot/apps.py
from django.apps import AppConfig

class ArbitrageBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.arbitrage_bot'
    label = 'arbitrage_bot'

    def ready(self):
        import apps.arbitrage_bot.signals