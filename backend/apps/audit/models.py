"""
Audit logging models for EROM System
Complete immutable audit trail of all system actions
"""
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel, User
import json


class AuditLog(TimeStampedModel):
    """
    Immutable audit trail
    NEVER UPDATE OR DELETE
    """
    # Action details
    action = models.CharField(
        max_length=20,
        choices=[
            ('create', 'Create'),
            ('update', 'Update'),
            ('delete', 'Delete'),
            ('login', 'Login'),
            ('logout', 'Logout'),
            ('reversal', 'Reversal'),
            ('approval', 'Approval'),
        ]
    )
    
    # What was affected
    model_name = models.CharField(max_length=100, help_text='Model class name')
    object_id = models.CharField(max_length=100, help_text='ID of the affected object')
    
    # State tracking
    before_state = models.JSONField(null=True, blank=True, help_text='State before action')
    after_state = models.JSONField(null=True, blank=True, help_text='State after action')
    
    # Context
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='audit_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Additional info
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.model_name}({self.object_id})"
    
    @classmethod
    def log_action(cls, user, action, model_name, object_id, before=None, after=None, notes='', request=None):
        """
        Helper method to create audit log entry
        """
        ip_address = None
        user_agent = ''
        
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            before_state=before,
            after_state=after,
            notes=notes,
            ip_address=ip_address,
            user_agent=user_agent
        )


class BackupLog(TimeStampedModel):
    """
    Track backup operations
    """
    backup_type = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual Backup'),
            ('automatic', 'Automatic Backup'),
            ('before_update', 'Pre-Update Backup'),
        ]
    )
    
    # Backup details
    file_path = models.CharField(max_length=500)
    file_size_bytes = models.BigIntegerField()
    checksum = models.CharField(max_length=64, help_text='SHA-256 checksum')
    
    # Encryption
    is_encrypted = models.BooleanField(default=True)
    encryption_algorithm = models.CharField(max_length=50, default='AES-256-GCM')
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='completed'
    )
    
    error_message = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='backups_created')
    
    class Meta:
        db_table = 'backup_log'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Backup {self.created_at.strftime('%Y-%m-%d %H:%M')} - {self.status}"


class SystemEvent(TimeStampedModel):
    """
    System-level events (startup, shutdown, errors)
    """
    event_type = models.CharField(
        max_length=20,
        choices=[
            ('startup', 'System Startup'),
            ('shutdown', 'System Shutdown'),
            ('error', 'System Error'),
            ('migration', 'Database Migration'),
            ('update', 'System Update'),
        ]
    )
    
    severity = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('critical', 'Critical'),
        ],
        default='info'
    )
    
    message = models.TextField()
    details = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'system_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['event_type']),
            models.Index(fields=['severity']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.severity} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
