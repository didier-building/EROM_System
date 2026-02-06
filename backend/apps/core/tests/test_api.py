"""
API test cases for authentication endpoints
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.core.models import User, Shop


class AuthenticationAPITests(TestCase):
    """Test authentication API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create shop
        self.shop = Shop.objects.create(
            name="Test Shop",
            owner_name="Owner",
            phone_number="+250788123456",
            license_key="TEST-KEY",
            device_id="test-device"
        )
        
        # Create users
        self.owner = User.objects.create(
            username="owner",
            full_name="Shop Owner",
            role=User.OWNER,
            is_active=True
        )
        self.owner.set_password("owner123")
        self.owner.save()
        
        self.cashier = User.objects.create(
            username="cashier",
            full_name="Cashier User",
            role=User.CASHIER,
            is_active=True
        )
        self.cashier.set_password("cashier123")
        self.cashier.save()
    
    def test_login_success(self):
        """Test successful login returns token and user data"""
        url = reverse('login')
        data = {
            'username': 'owner',
            'password': 'owner123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('token', response.data['data'])
        self.assertIn('user', response.data['data'])
        self.assertEqual(response.data['data']['user']['username'], 'owner')
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password fails"""
        url = reverse('login')
        data = {
            'username': 'owner',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent username fails"""
        url = reverse('login')
        data = {
            'username': 'nonexistent',
            'password': 'password123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
    
    def test_login_inactive_user(self):
        """Test login with inactive user fails"""
        self.owner.is_active = False
        self.owner.save()
        
        url = reverse('login')
        data = {
            'username': 'owner',
            'password': 'owner123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout(self):
        """Test logout invalidates token"""
        # Login first
        token = self.owner.generate_session_token()
        
        # Logout
        url = reverse('logout')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify token is cleared
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.session_token, '')
    
    def test_me_endpoint(self):
        """Test /me endpoint returns current user"""
        token = self.owner.generate_session_token()
        
        url = reverse('me')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'owner')
        self.assertEqual(response.data['role'], User.OWNER)
    
    def test_unauthenticated_access_denied(self):
        """Test endpoints require authentication"""
        url = reverse('me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_expired_token_rejected(self):
        """Test expired token is rejected"""
        from datetime import timedelta
        from django.utils import timezone
        
        token = self.owner.generate_session_token()
        self.owner.session_expires_at = timezone.now() - timedelta(hours=1)
        self.owner.save()
        
        url = reverse('me')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
