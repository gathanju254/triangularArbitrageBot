# backend/apps/users/validators.py
from django.urls import path

from ..views.web_views import (
    NotificationWebView,
    mark_all_read_web,
    notification_detail
)

app_name = 'notifications'

urlpatterns = [
    path('', NotificationWebView.as_view(), name='list'),
    path('mark-all-read/', mark_all_read_web, name='mark-all-read'),
    path('<int:pk>/', notification_detail, name='detail'),
]