"""
Custom authentication for desktop app
Token-based authentication without external dependencies
"""
from rest_framework import authentication, exceptions
from django.utils import timezone
from .models import User


class DesktopTokenAuthentication(authentication.BaseAuthentication):
    """
    Simple token authentication for desktop app
    Token passed in Authorization header: Token <token>
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Token '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            user = User.objects.get(session_token=token, is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')
        
        # Check if token expired
        if not user.is_session_valid():
            raise exceptions.AuthenticationFailed('Token expired')
        
        return (user, None)
    
    def authenticate_header(self, request):
        return 'Token'
