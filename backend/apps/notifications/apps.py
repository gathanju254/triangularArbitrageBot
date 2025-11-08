# backend/apps/notifications/apps.py

from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'Notifications'

    def ready(self):
        # Import signals module but don't fail if models aren't available yet
        try:
            import apps.notifications.signals
            print("Notifications signals imported successfully")
        except Exception as e:
            print(f"Notifications signals import warning: {e}")
            print("Notifications will work with basic functionality")