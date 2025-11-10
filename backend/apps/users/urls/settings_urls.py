# backend/apps/users/urls/settings_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views.settings_views import UserSettingsViewSet, BotConfigurationViewSet

router = DefaultRouter()
router.register(r'settings', UserSettingsViewSet, basename='user-settings')
router.register(r'bot-config', BotConfigurationViewSet, basename='bot-config')

urlpatterns = [
    path('', include(router.urls)),
]