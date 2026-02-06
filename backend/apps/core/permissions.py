"""
Permission classes for role-based access control
"""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permission class that only allows owners
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_owner


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows owners full access, cashiers read-only
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read operations allowed for all
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write operations only for owners
        return request.user.is_owner


class IsCashierOrOwner(permissions.BasePermission):
    """
    Permission class that allows both owners and cashiers
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
