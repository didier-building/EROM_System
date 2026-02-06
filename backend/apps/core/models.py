"""
Core models for EROM System
Base models for user management and shop configuration
"""
from django.db import models
from django.utils import timezone
from argon2 import PasswordHasher
import secrets


class TimeStampedModel(models.Model):
    """
    Abstract base model with created_at and updated_at fields
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Shop(TimeStampedModel):
    """
    Shop configuration and license information
    Single record per installation
    """
    name = models.CharField(max_length=200)
    owner_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    
    # License information
    license_key = models.CharField(max_length=100, unique=True)
    license_activated_at = models.DateTimeField(default=timezone.now)
    license_expires_at = models.DateTimeField(null=True, blank=True)  # Null = lifetime
    
    # Device registration
    device_id = models.CharField(max_length=200, unique=True)
    max_devices = models.IntegerField(default=1)
    
    # System configuration
    currency = models.CharField(max_length=10, default='RWF')
    timezone = models.CharField(max_length=50, default='Africa/Kigali')
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'shop_config'
        verbose_name = 'Shop Configuration'
        verbose_name_plural = 'Shop Configuration'
    
    def __str__(self):
        return self.name


class User(TimeStampedModel):
    """
    User model for Owner and Cashier/Manager roles
    Simplified for desktop app - no email required
    """
    OWNER = 'owner'
    CASHIER = 'cashier'
    
    ROLE_CHOICES = [
        (OWNER, 'Owner'),
        (CASHIER, 'Cashier/Manager'),
    ]
    
    username = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=200)
    full_name = models.CharField(max_length=200)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Current session token (single device login)
    session_token = models.CharField(max_length=100, blank=True)
    session_expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} ({self.role})"
    
    def set_password(self, raw_password):
        """
        Hash password using Argon2
        """
        ph = PasswordHasher()
        self.password_hash = ph.hash(raw_password)
    
    def check_password(self, raw_password):
        """
        Verify password against hash
        """
        ph = PasswordHasher()
        try:
            ph.verify(self.password_hash, raw_password)
            # Rehash if parameters changed
            if ph.check_needs_rehash(self.password_hash):
                self.set_password(raw_password)
                self.save(update_fields=['password_hash'])
            return True
        except Exception:
            return False
    
    def generate_session_token(self):
        """
        Generate a new session token
        """
        self.session_token = secrets.token_urlsafe(32)
        self.session_expires_at = timezone.now() + timezone.timedelta(hours=12)
        self.last_login = timezone.now()
        self.save(update_fields=['session_token', 'session_expires_at', 'last_login'])
        return self.session_token
    
    def is_session_valid(self):
        """
        Check if current session token is valid
        """
        if not self.session_token or not self.session_expires_at:
            return False
        return timezone.now() < self.session_expires_at
    
    @property
    def is_owner(self):
        return self.role == self.OWNER
    
    @property
    def is_cashier(self):
        return self.role == self.CASHIER
