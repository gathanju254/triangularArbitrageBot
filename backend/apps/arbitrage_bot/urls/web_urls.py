# backend/apps/arbitrage_bot/urls/web_urls.py
from django.urls import path
from ..views.web_views import *

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('trading/', trading_view, name='trading'),
    path('settings/', settings_view, name='settings'),
    path('analytics/', analytics_view, name='analytics'),
]