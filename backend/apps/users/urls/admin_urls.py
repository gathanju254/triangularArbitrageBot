# backend/apps/users/urls/admin_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views.admin_views import (
    UserAdminViewSet,
    APIKeyAdminViewSet,
    AdminDashboardView
)

# Create router for Admin ViewSets
admin_router = DefaultRouter()
admin_router.register(r'users', UserAdminViewSet, basename='admin-user')
admin_router.register(r'api-keys', APIKeyAdminViewSet, basename='admin-apikey')

admin_urlpatterns = [
    # Admin dashboard
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    
    # Include admin router URLs
    path('', include(admin_router.urls)),
    
    # Admin-specific actions
    path('users/<int:pk>/deactivate/', 
         UserAdminViewSet.as_view({'post': 'deactivate'}), 
         name='admin-user-deactivate'),
    path('users/statistics/', 
         UserAdminViewSet.as_view({'get': 'statistics'}), 
         name='admin-user-statistics'),
    path('users/search/', 
         UserAdminViewSet.as_view({'get': 'search'}), 
         name='admin-user-search'),
    path('api-keys/statistics/', 
         APIKeyAdminViewSet.as_view({'get': 'statistics'}), 
         name='admin-apikey-statistics'),
    path('api-keys/bulk-validate/', 
         APIKeyAdminViewSet.as_view({'post': 'bulk_validate'}), 
         name='admin-apikey-bulk-validate'),
]

urlpatterns = admin_urlpatterns