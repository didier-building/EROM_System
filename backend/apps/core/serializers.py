"""
Serializers for authentication and user management
"""
from rest_framework import serializers
from .models import User, Shop


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'role', 'is_active', 'last_login', 'created_at']
        read_only_fields = ['id', 'last_login', 'created_at']


class LoginSerializer(serializers.Serializer):
    """
    Serializer for login request
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ShopSerializer(serializers.ModelSerializer):
    """
    Serializer for Shop configuration
    """
    class Meta:
        model = Shop
        fields = [
            'id', 'name', 'owner_name', 'phone_number', 'address',
            'license_key', 'license_activated_at', 'license_expires_at',
            'currency', 'timezone', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'license_activated_at', 'created_at']
