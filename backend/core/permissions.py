# backend/core/permissions.py

from rest_framework import permissions
from django.conf import settings

class IsAdminUser(permissions.BasePermission):
    """
    Permission to only allow admin users to access.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_staff

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners or admins to access objects.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users can do anything
        if request.user and request.user.is_staff:
            return True
        
        # Check if the object has a user attribute and it matches the request user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For objects that don't have a direct user reference, check by ID
        if hasattr(obj, 'id'):
            return obj.id == request.user.id
        
        return False

class IsTraderOrAdmin(permissions.BasePermission):
    """
    Permission to only allow traders and admins to access trading features.
    """
    
    def has_permission(self, request, view):
        return request.user and (
            request.user.is_staff or 
            getattr(request.user, 'user_type', None) in ['admin', 'trader']
        )

class IsVerifiedUser(permissions.BasePermission):
    """
    Permission to only allow verified users.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # If email verification is required, check if user is verified
        if getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', False):
            return getattr(request.user, 'is_verified', True)
        
        return True

class IsTradingEnabled(permissions.BasePermission):
    """
    Permission to check if trading is enabled for the user.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has trading enabled in their profile
        if hasattr(request.user, 'profile'):
            # This would depend on your UserProfile model structure
            # For now, assume trading is enabled by default
            return True
        
        return False

class ReadOnly(permissions.BasePermission):
    """
    Permission to only allow read-only operations.
    """
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

class IsService(permissions.BasePermission):
    """
    Permission for internal service-to-service communication.
    """
    
    def has_permission(self, request, view):
        # Check for service API key in header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        service_key = getattr(settings, 'SERVICE_API_KEY', None)
        
        if service_key and auth_header.startswith('APIKey '):
            provided_key = auth_header.split(' ')[1]
            return provided_key == service_key
        
        return False

class HasExchangeAccess(permissions.BasePermission):
    """
    Permission to check if user has access to a specific exchange.
    """
    
    def has_permission(self, request, view):
        # Get exchange from view kwargs or query params
        exchange = view.kwargs.get('exchange') or request.query_params.get('exchange')
        
        if not exchange:
            return True  # No specific exchange required
        
        # Check if user has API keys for this exchange
        if hasattr(request.user, 'api_keys'):
            return request.user.api_keys.filter(
                exchange=exchange, 
                is_active=True
            ).exists()
        
        return False

class RiskPermission(permissions.BasePermission):
    """
    Permission that checks risk management rules before allowing actions.
    """
    
    def has_permission(self, request, view):
        # Skip risk checks for read-only operations
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Import here to avoid circular imports
        from apps.risk_management.services import RiskService
        
        try:
            # Check if the action would violate risk limits
            risk_service = RiskService(request.user)
            return risk_service.check_trade_permission(request.data)
        except Exception:
            # If risk service is unavailable, deny permission for safety
            return False

class CompoundPermission(permissions.BasePermission):
    """
    Combine multiple permissions with AND logic.
    """
    
    def __init__(self, *permission_classes):
        self.permission_classes = permission_classes
    
    def has_permission(self, request, view):
        return all(
            permission().has_permission(request, view)
            for permission in self.permission_classes
        )
    
    def has_object_permission(self, request, view, obj):
        return all(
            permission().has_object_permission(request, view, obj)
            for permission in self.permission_classes
        )