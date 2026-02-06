"""
Licensing and activation models for EROM System
"""
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel, User
import hashlib
import secrets


class License(TimeStampedModel):
    """
    License key management
    """
    # License key (format: EROM-XXXX-XXXX-XXXX-XXXX)
    license_key = models.CharField(max_length=50, unique=True)
    
    # License details
    license_type = models.CharField(
        max_length=20,
        choices=[
            ('lifetime', 'Lifetime'),
            ('annual', 'Annual'),
            ('trial', 'Trial'),
        ],
        default='lifetime'
    )
    
    # Validity
    issued_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(null=True, blank=True)  # Null = lifetime
    
    # Activation
    is_activated = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)
    activation_count = models.IntegerField(default=0)
    max_activations = models.IntegerField(default=1, help_text='Number of devices allowed')
    
    # Customer info (stored during sale)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.CharField(max_length=200, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    revocation_reason = models.TextField(blank=True)
    
    # Tracking
    issued_by = models.CharField(max_length=200, default='EROM_SYSTEM')
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'licenses'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.license_key} - {self.license_type}"
    
    @classmethod
    def generate_license_key(cls):
        """
        Generate a unique license key
        Format: EROM-XXXX-XXXX-XXXX-XXXX
        """
        while True:
            # Generate random parts
            parts = [
                ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(4))
                for _ in range(4)
            ]
            license_key = f"EROM-{'-'.join(parts)}"
            
            # Check if unique
            if not cls.objects.filter(license_key=license_key).exists():
                return license_key
    
    def can_activate(self):
        """Check if license can be activated"""
        if not self.is_active:
            return False, "License is revoked"
        
        if self.expiry_date and self.expiry_date < timezone.now():
            return False, "License has expired"
        
        if self.activation_count >= self.max_activations:
            return False, "Maximum activations reached"
        
        return True, "OK"
    
    def activate(self, device_id):
        """Activate license for a device"""
        can_activate, message = self.can_activate()
        if not can_activate:
            return False, message
        
        # Create activation record
        activation = LicenseActivation.objects.create(
            license=self,
            device_id=device_id,
            activation_date=timezone.now()
        )
        
        # Update license
        self.is_activated = True
        self.activated_at = timezone.now()
        self.activation_count += 1
        self.save()
        
        return True, activation


class LicenseActivation(TimeStampedModel):
    """
    Track license activations per device
    """
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name='activations')
    
    # Device info
    device_id = models.CharField(max_length=200, unique=True, help_text='Hardware fingerprint')
    device_name = models.CharField(max_length=200, blank=True)
    
    # Activation details
    activation_date = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)
    
    # Status
    is_active = models.BooleanField(default=True)
    deactivation_date = models.DateTimeField(null=True, blank=True)
    deactivation_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'license_activations'
        ordering = ['-activation_date']
    
    def __str__(self):
        return f"{self.license.license_key} - {self.device_id}"
    
    def deactivate(self, reason=''):
        """Deactivate this device"""
        self.is_active = False
        self.deactivation_date = timezone.now()
        self.deactivation_reason = reason
        self.save()
        
        # Decrease activation count on license
        self.license.activation_count = max(0, self.license.activation_count - 1)
        self.license.save()
