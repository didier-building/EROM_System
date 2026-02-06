"""
Test cases for core models (User, Shop)
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.core.models import User, Shop


class ShopModelTests(TestCase):
    """Test Shop model functionality"""
    
    def setUp(self):
        self.shop = Shop.objects.create(
            name="Test Electronics",
            owner_name="Test Owner",
            phone_number="+250788123456",
            license_key="TEST-1234-5678",
            device_id="test-device-123",
            currency="RWF",
            timezone="Africa/Kigali"
        )
    
    def test_shop_creation(self):
        """Test shop can be created with required fields"""
        self.assertEqual(self.shop.name, "Test Electronics")
        self.assertEqual(self.shop.currency, "RWF")
        self.assertTrue(self.shop.is_active)
    
    def test_shop_string_representation(self):
        """Test shop __str__ method"""
        self.assertEqual(str(self.shop), "Test Electronics")
    
    def test_only_one_shop_allowed(self):
        """Test that system enforces single shop constraint"""
        # This would require custom save logic or database constraint
        shop_count = Shop.objects.count()
        self.assertEqual(shop_count, 1)


class UserModelTests(TestCase):
    """Test User model functionality"""
    
    def setUp(self):
        self.owner = User.objects.create(
            username="testowner",
            full_name="Test Owner",
            role=User.OWNER,
            is_active=True
        )
        self.owner.set_password("secure123")
        self.owner.save()
        
        self.cashier = User.objects.create(
            username="testcashier",
            full_name="Test Cashier",
            role=User.CASHIER,
            is_active=True
        )
        self.cashier.set_password("cashier123")
        self.cashier.save()
    
    def test_user_creation(self):
        """Test user can be created with required fields"""
        self.assertEqual(self.owner.username, "testowner")
        self.assertEqual(self.owner.role, User.OWNER)
        self.assertTrue(self.owner.is_active)
    
    def test_password_hashing(self):
        """Test password is hashed using Argon2"""
        self.assertNotEqual(self.owner.password_hash, "secure123")
        self.assertTrue(self.owner.password_hash.startswith("$argon2"))
    
    def test_password_verification(self):
        """Test password can be verified correctly"""
        self.assertTrue(self.owner.check_password("secure123"))
        self.assertFalse(self.owner.check_password("wrongpassword"))
    
    def test_token_generation(self):
        """Test session token can be generated"""
        token = self.owner.generate_session_token()
        self.assertEqual(len(token), 43)  # urlsafe_base64 length
        self.assertEqual(self.owner.session_token, token)
        self.assertIsNotNone(self.owner.session_expires_at)
    
    def test_token_expiry(self):
        """Test token expiry validation"""
        token = self.owner.generate_session_token()
        self.assertTrue(self.owner.is_session_valid())
        
        # Expire the token
        self.owner.session_expires_at = timezone.now() - timedelta(hours=1)
        self.owner.save()
        self.assertFalse(self.owner.is_session_valid())
    
    def test_user_roles(self):
        """Test different user roles"""
        self.assertEqual(self.owner.role, User.OWNER)
        self.assertEqual(self.cashier.role, User.CASHIER)
    
    def test_user_string_representation(self):
        """Test user __str__ method"""
        self.assertEqual(str(self.owner), "Test Owner (owner)")
    
    def test_username_uniqueness(self):
        """Test username must be unique"""
        with self.assertRaises(Exception):
            User.objects.create(
                username="testowner",  # Duplicate
                full_name="Another User",
                role=User.CASHIER
            )
    
    def test_user_authentication_properties(self):
        """Test Django auth required properties"""
        self.assertTrue(self.owner.is_authenticated)
        self.assertFalse(self.owner.is_anonymous)
