# backend/apps/users/permissions.py

from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners or admins to access objects"""
    
    def has_object_permission(self, request, view, obj):
        # Check if user is admin
        if request.user and request.user.is_staff:
            return True
        
        # Check if user is owner of the object
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False

class IsTraderOrAdmin(permissions.BasePermission):
    """Allow only traders and admins to access trading features"""
    
    def has_permission(self, request, view):
        return request.user and (
            request.user.is_staff or 
            getattr(request.user, 'user_type', None) in ['admin', 'trader']
        )