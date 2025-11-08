# backend/apps/users/validators.py
from django.urls import path

from ..views.admin_views import (
    NotificationAdminView,
    admin_notification_stats
)

app_name = 'admin_notifications'

urlpatterns = [
    path('dashboard/', NotificationAdminView.as_view(), name='dashboard'),
    path('stats/', admin_notification_stats, name='stats'),
]