"""
Sales and transaction models for EROM System
POS transactions and append-only transaction ledger
"""
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel, User
from apps.inventory.models import Product


class Transaction(TimeStampedModel):
    """
    Append-only ledger of all sales transactions
    NEVER UPDATE OR DELETE - only INSERT
    """
    SALE = 'sale'
    PURCHASE = 'purchase'
    RETURN = 'return'
    REVERSAL = 'reversal'
    
    # Payment method constants
    CASH = 'cash'
    MOBILE_MONEY = 'mobile_money'
    BANK_TRANSFER = 'bank_transfer'
    CARD = 'card'
    CREDIT = 'credit'
    
    TRANSACTION_TYPES = [
        (SALE, 'Sale'),
        (PURCHASE, 'Purchase'),
        (RETURN, 'Return'),
        (REVERSAL, 'Reversal/Correction'),
    ]
    
    # Transaction identification
    transaction_id = models.CharField(max_length=50, unique=True, help_text='AUTO: TXN-YYYYMMDD-NNNN')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    transaction_date = models.DateTimeField(default=timezone.now)
    
    # Financial details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('cash', 'Cash'),
            ('mobile_money', 'Mobile Money'),
            ('bank_transfer', 'Bank Transfer'),
            ('credit', 'Credit/Agent'),
        ],
        default='cash'
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    change_given = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Customer info (optional)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Reversal tracking
    reversal_of = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='reversals'
    )
    reversal_reason = models.TextField(blank=True)
    reversal_approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='approved_transaction_reversals'
    )
    
    # Tracking
    processed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='transactions_processed')
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['-transaction_date']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['processed_by', '-transaction_date']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type} - {self.total_amount} RWF"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate transaction ID: TXN-20260206-0001
            today = timezone.now().strftime('%Y%m%d')
            last_txn = Transaction.objects.filter(
                transaction_id__startswith=f'TXN-{today}'
            ).order_by('-transaction_id').first()
            
            if last_txn:
                last_num = int(last_txn.transaction_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.transaction_id = f'TXN-{today}-{new_num:04d}'
        
        super().save(*args, **kwargs)


class TransactionItem(TimeStampedModel):
    """
    Line items for each transaction
    Append-only
    """
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='transaction_items')
    
    # Item details
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'transaction_items'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.transaction.transaction_id} - {self.product.name} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate line total
        self.line_total = (self.unit_price * self.quantity) - self.discount
        super().save(*args, **kwargs)


class Reconciliation(TimeStampedModel):
    """
    Blind count reconciliation records
    Tracks physical vs system stock counts
    """
    # Status constants
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    PENDING = 'in_progress'  # Alias for backward compatibility
    
    reconciliation_date = models.DateTimeField(default=timezone.now)
    reconciliation_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily Count'),
            ('weekly', 'Weekly Count'),
            ('monthly', 'Monthly Count'),
            ('spot_check', 'Spot Check'),
        ],
        default='daily'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='in_progress'
    )
    
    # Tracking
    performed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reconciliations_performed')
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='reconciliations_approved'
    )
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'reconciliations'
        ordering = ['-reconciliation_date']
    
    def __str__(self):
        return f"Reconciliation {self.reconciliation_date.strftime('%Y-%m-%d')} - {self.status}"
    
    @property
    def total_discrepancies(self):
        """Count items with discrepancies"""
        return self.items.filter(has_discrepancy=True).count()


class ReconciliationItem(TimeStampedModel):
    """
    Individual product counts in reconciliation
    """
    reconciliation = models.ForeignKey(Reconciliation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    
    # Counts
    system_count = models.IntegerField(help_text='Count per system')
    physical_count = models.IntegerField(help_text='Actual count')
    variance = models.IntegerField(help_text='Difference (physical - system)')
    
    # Analysis
    has_discrepancy = models.BooleanField(default=False)
    discrepancy_reason = models.TextField(blank=True)
    
    # Correction
    correction_approved = models.BooleanField(default=False)
    correction_created = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'reconciliation_items'
        unique_together = ['reconciliation', 'product']
    
    def __str__(self):
        return f"{self.product.name} - Variance: {self.variance}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate variance and discrepancy flag
        self.variance = self.physical_count - self.system_count
        self.has_discrepancy = self.variance != 0
        super().save(*args, **kwargs)
