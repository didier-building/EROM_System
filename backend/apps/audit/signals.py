"""
Signals for automatic audit logging
Tracks all model changes
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.serializers import serialize
import json


# We'll implement audit signals after all models are created
# This prevents circular import issues

def log_model_change(sender, instance, action, user=None, before_state=None):
    """
    Helper function to log model changes to audit log
    """
    from apps.audit.models import AuditLog
    
    # Skip audit log entries to prevent recursion
    if sender.__name__ == 'AuditLog':
        return
    
    # Serialize the instance
    after_state = None
    if action != 'delete':
        try:
            serialized = serialize('json', [instance])
            after_state = json.loads(serialized)[0]['fields']
        except:
            after_state = {'id': str(instance.pk)}
    
    # Create audit log entry
    if user:
        AuditLog.log_action(
            user=user,
            action=action,
            model_name=sender.__name__,
            object_id=instance.pk,
            before=before_state,
            after=after_state
        )


# Signals will be connected in the ready() method of the app config
# to ensure all models are loaded first
