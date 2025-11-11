# backend/apps/risk_management/apps.py
from django.apps import AppConfig

class RiskManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.risk_management'

    def ready(self):
        import apps.risk_management.signals