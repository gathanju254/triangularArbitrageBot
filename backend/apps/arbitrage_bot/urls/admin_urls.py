# backend/apps/arbitrage_bot/urls/admin_urls.py
from django.urls import path
from ..views.admin_views import *

urlpatterns = [
    path('overview/', admin_system_overview, name='admin_system_overview'),
    # Add more admin URLs as needed
]