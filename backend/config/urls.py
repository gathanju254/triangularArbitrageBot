# backend/config/urls.py
"""
URL configuration for triangularArbitrageBot project.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.arbitrage_bot.urls.web_urls')),  # Web views at root
    path('api/', include('apps.arbitrage_bot.urls.api_urls')),  # API endpoints
    path('admin-tools/', include('apps.arbitrage_bot.urls.admin_urls')),  # Admin tools
    
    # User URLs - using separate includes
    path('user-tools/admin/', include('apps.users.urls.admin_urls')),  # Admin user tools
    path('api/users/', include('apps.users.urls.api_urls')),  # User API endpoints
    path('accounts/', include('apps.users.urls.web_urls')),  # Authentication / user web UI
    
    # Notification URLs - integrated into TAB
    path('api/notifications/', include('apps.notifications.urls.api_urls')),  # Notification API endpoints
    path('notifications/', include('apps.notifications.urls.web_urls')),  # Notification web views
    path('admin/notifications/', include('apps.notifications.urls.admin_urls')),  # Admin notification tools
]