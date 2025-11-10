# backend/config/urls.py
"""
URL configuration for triangularArbitrageBot project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.arbitrage_bot.urls.web_urls')),  # Web views at root
    path('api/arbitrage/', include('apps.arbitrage_bot.urls.api_urls')),  # Arbitrage API endpoints
    path('api/', include('apps.arbitrage_bot.urls.api_urls')),  # Also include at root api
    path('admin-tools/', include('apps.arbitrage_bot.urls.admin_urls')),  # Admin tools
    
    # User URLs - Updated to include settings URLs
    path('user-tools/admin/', include('apps.users.urls.admin_urls')),
    path('api/users/', include('apps.users.urls.api_urls')),
    path('api/settings/', include('apps.users.urls.settings_urls')),  # Add settings URLs
    path('api/auth/', include('apps.users.urls.web_urls')),
    
    # Notification URLs
    path('api/notifications/', include('apps.notifications.urls.api_urls')),
    path('notifications/', include('apps.notifications.urls.web_urls')),
    path('admin/notifications/', include('apps.notifications.urls.admin_urls')),
]