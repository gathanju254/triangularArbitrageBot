# backend/apps/users/validators.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views import (
    NotificationViewSet,
    AdminNotificationViewSet,
    NotificationDebugView,
    TestNotificationView
)

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'admin/notifications', AdminNotificationViewSet, basename='admin-notification')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Debug and test endpoints
    path('debug/', NotificationDebugView.as_view(), name='notifications-debug'),
    path('test/', TestNotificationView.as_view(), name='test-notification'),
    
    # Legacy endpoints for backward compatibility
    path('unread/', NotificationViewSet.as_view({'get': 'unread'}), name='notifications-unread'),
    path('mark-all-read/', NotificationViewSet.as_view({'post': 'mark_all_read'}), name='notifications-mark-all-read'),
    path('stats/', NotificationViewSet.as_view({'get': 'stats'}), name='notifications-stats'),
]