# backend/apps/users/urls.py
from django.urls import path, include

urlpatterns = [
    # API URLs (REST endpoints)
    path('api/', include('apps.users.urls.api_urls')),
    
    # Web URLs (HTML pages & authentication)
    path('web/', include('apps.users.urls.web_urls')),
    
    # Admin URLs (staff only)
    path('admin/', include('apps.users.urls.admin_urls')),
    
    # Health check (available at root)
    path('health/', include('apps.users.urls.health_urls')),
]