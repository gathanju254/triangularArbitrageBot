# backend/apps/users/urls/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views.web_views import register_user, login_user, logout_user
from ..views.api_views import (
    UserViewSet, 
    APIKeyViewSet, 
    ChangePasswordView,
    APIKeyBulkOperationsView, 
    APIKeyExportView, 
    APIKeyRotationView,
    UserDashboardView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'api-keys', APIKeyViewSet, basename='apikey')


api_urlpatterns = [
    # User management
    path('', include(router.urls)),

    # Profile endpoints
    path('profile/', UserViewSet.as_view({'get': 'profile'}), name='user-profile'),
    path('update_profile/', UserViewSet.as_view({'put': 'update_profile', 'patch': 'update_profile'}), name='user-update-profile'),

    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('register/', register_user, name='register'),
    
    # Password management
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Dashboard
    path('dashboard/', UserDashboardView.as_view(), name='user-dashboard'),
    
    # API Keys management
    path('api-keys/bulk-operations/', APIKeyBulkOperationsView.as_view(), name='api-key-bulk-operations'),
    path('api-keys/export/', APIKeyExportView.as_view(), name='api-key-export'),
    path('api-keys/rotate-encryption/', APIKeyRotationView.as_view(), name='api-key-rotation'),
]

urlpatterns = api_urlpatterns