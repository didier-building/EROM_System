"""
Views for authentication and user management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone

from .models import User, Shop
from .serializers import UserSerializer, LoginSerializer, ShopSerializer
from .permissions import IsOwner


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login endpoint - returns user info and session token
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    try:
        user = User.objects.get(username=username, is_active=True)
    except User.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.check_password(password):
        return Response(
            {'success': False, 'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Generate new session token
    token = user.generate_session_token()
    
    return Response({
        'success': True,
        'data': {
            'token': token,
            'user': UserSerializer(user).data
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint - invalidates current session token
    """
    user = request.user
    user.session_token = ''
    user.session_expires_at = None
    user.save(update_fields=['session_token', 'session_expires_at'])
    
    return Response({
        'success': True,
        'message': 'Logged out successfully'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Get current user information
    """
    return Response({
        'success': True,
        'data': UserSerializer(request.user).data
    })


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users (Owner only)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwner]
    
    def create(self, request, *args, **kwargs):
        """
        Create new user with password
        """
        data = request.data
        password = data.pop('password', None)
        
        if not password:
            return Response(
                {'success': False, 'error': 'Password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        user.set_password(password)
        user.save()
        
        return Response({
            'success': True,
            'data': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """
        Change user password (Owner only)
        """
        user = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response(
                {'success': False, 'error': 'New password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        })


class ShopViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for shop configuration (read-only for most operations)
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Get current shop configuration
        """
        shop = Shop.objects.first()
        if not shop:
            return Response(
                {'success': False, 'error': 'Shop not configured'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'success': True,
            'data': ShopSerializer(shop).data
        })
