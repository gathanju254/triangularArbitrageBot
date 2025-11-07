# backend/apps/users/urls/health_urls.py
from django.urls import path
from ..views.web_views import redis_health_check

health_urlpatterns = [
    path('redis/', redis_health_check, name='redis-health'),
]

urlpatterns = health_urlpatterns