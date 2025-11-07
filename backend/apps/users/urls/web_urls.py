# backend/apps/users/urls/web_urls.py
from django.urls import path
from ..views.web_views import (
    register_user,
    login_user,
    logout_user,
    reset_password_request,
    reset_password_confirm,
    validate_exchange_credentials,
    profile_view,
    api_keys_view,
    dashboard_view
)

web_urlpatterns = [
    # Authentication endpoints
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    
    # Password management
    path('reset-password/', reset_password_request, name='reset-password'),
    path('reset-password/confirm/', reset_password_confirm, name='reset-password-confirm'),
    
    # Exchange credentials validation
    path('validate-exchange-credentials/', validate_exchange_credentials, name='validate-exchange-credentials'),
    
    # Django Template Views (for web interface)
    path('profile/', profile_view, name='profile'),
    path('api-keys/', api_keys_view, name='api-keys-web'),
    path('dashboard/', dashboard_view, name='dashboard-web'),
]

urlpatterns = web_urlpatterns