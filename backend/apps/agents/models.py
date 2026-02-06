"""
Agent and consignment tracking models for EROM System
Tracks stock transfers to field technicians and debt management
"""
from django.db import models
from django.db.models import Sum, Q
from django.utils import timezone
from apps.core.models import TimeStampedModel, User
from apps.inventory.models import Product


class Agent(TimeStampedModel):
    """
    Field technicians who take parts on consignment
    """
    # Basic info
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    id_number = models.CharField(max_length=50, blank=True, help_text='National ID or business registration')
    
    # Location
    address = models.TextField(blank=True)
    area = models.CharField(max_length=100, blank=True, help_text='Working area/district')
    
    # Business details
    business_name = models.CharField(max_length=200, blank=True)
    
    # Credit management
    credit_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Maximum debt allowed (0 = unlimited)'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_trusted = models.BooleanField(default=False, help_text='Trusted agents have higher credit limits')
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='agents_created')
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'agents'
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.full_name
    
    @property
    def total_debt(self):
        """Calculate total outstanding debt"""
        return self.ledger_entries.filter(
            is_paid=False
        ).aggregate(
            total=Sum('debt_amount')
        )['total'] or 0
    
    @property
    def can_take_more_stock(self):
        """Check if agent can take more stock based on credit limit"""
        if self.credit_limit == 0:  # Unlimited
            return True
        return self.total_debt < self.credit_limit
    
    def get_debt_by_age(self):
        """Get debt categorized by age (7, 30, 60, 90+ days)"""
        now = timezone.now()
        
        return {
            '0-7': self.ledger_entries.filter(
                is_paid=False,
                transfer_date__gte=now - timezone.timedelta(days=7)
            ).aggregate(total=Sum('debt_amount'))['total'] or 0,
            
            '8-30': self.ledger_entries.filter(
                is_paid=False,
                transfer_date__gte=now - timezone.timedelta(days=30),
                transfer_date__lt=now - timezone.timedelta(days=7)
            ).aggregate(total=Sum('debt_amount'))['total'] or 0,
            
            '31-60': self.ledger_entries.filter(
                is_paid=False,
                transfer_date__gte=now - timezone.timedelta(days=60),
                transfer_date__lt=now - timezone.timedelta(days=30)
            ).aggregate(total=Sum('debt_amount'))['total'] or 0,
            
            '61-90': self.ledger_entries.filter(
                is_paid=False,
                transfer_date__gte=now - timezone.timedelta(days=90),
                transfer_date__lt=now - timezone.timedelta(days=60)
            ).aggregate(total=Sum('debt_amount'))['total'] or 0,
            
            '90+': self.ledger_entries.filter(
                is_paid=False,
                transfer_date__lt=now - timezone.timedelta(days=90)
            ).aggregate(total=Sum('debt_amount'))['total'] or 0,
        }


class AgentLedger(TimeStampedModel):
    """
    Append-only ledger of stock transfers to agents
    NEVER UPDATE OR DELETE - only INSERT
    """
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='ledger_entries')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='agent_transfers')
    
    # Transfer details
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    debt_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text='Total amount owed')
    
    transfer_date = models.DateTimeField(default=timezone.now)
    
    # Payment tracking
    is_paid = models.BooleanField(default=False)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Reference to inventory movement
    inventory_movement_id = models.CharField(max_length=100, blank=True)
    
    # Tracking
    transferred_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='agent_transfers')
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'agent_ledger'
        ordering = ['-transfer_date']
        indexes = [
            models.Index(fields=['agent', '-transfer_date']),
            models.Index(fields=['is_paid']),
            models.Index(fields=['transfer_date']),
        ]
    
    def __str__(self):
        return f"{self.agent.full_name} - {self.product.name} ({self.quantity})"
    
    @property
    def remaining_debt(self):
        """Calculate remaining unpaid amount"""
        return self.debt_amount - self.paid_amount
    
    @property
    def days_outstanding(self):
        """Calculate how many days the debt has been outstanding"""
        if self.is_paid:
            return 0
        return (timezone.now() - self.transfer_date).days


class AgentPayment(TimeStampedModel):
    """
    Append-only ledger of payments from agents
    NEVER UPDATE OR DELETE - only INSERT
    """
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('cash', 'Cash'),
            ('mobile_money', 'Mobile Money'),
            ('bank_transfer', 'Bank Transfer'),
        ],
        default='cash'
    )
    
    # Reference
    reference_number = models.CharField(max_length=100, blank=True, help_text='Transaction reference')
    
    # Tracking
    received_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='agent_payments_received')
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'agent_payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.agent.full_name} - {self.amount} RWF"
