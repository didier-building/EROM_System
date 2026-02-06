"""
Inventory models for EROM System
Products, categories, and stock movements (append-only)
"""
from django.db import models
from apps.core.models import TimeStampedModel, User


class Category(TimeStampedModel):
    """
    Product categories (e.g., Screens, Batteries, Cameras, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Brand(TimeStampedModel):
    """
    Smartphone brands (Samsung, Apple, Tecno, Infinix, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'brands'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Model(TimeStampedModel):
    """
    Smartphone models (iPhone 13, Galaxy S21, etc.)
    """
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=150)
    model_number = models.CharField(max_length=100, blank=True)
    release_year = models.IntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='models/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'phone_models'
        unique_together = ['brand', 'name']
        ordering = ['brand__name', 'name']
    
    def __str__(self):
        return f"{self.brand.name} {self.name}"


class Product(TimeStampedModel):
    """
    Products/spare parts in inventory
    """
    # Identification
    sku = models.CharField(max_length=50, unique=True, help_text='Stock Keeping Unit')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Classification
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, null=True, blank=True)
    phone_model = models.ForeignKey(Model, on_delete=models.PROTECT, null=True, blank=True)
    
    # Inventory
    quantity_in_stock = models.IntegerField(default=0)
    quantity_in_field = models.IntegerField(default=0, help_text='Stock with agents')
    reorder_level = models.IntegerField(default=5, help_text='Alert when stock below this')
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Media
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # Barcode (optional)
    barcode = models.CharField(max_length=50, blank=True, unique=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='products_created')
    
    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['barcode']),
        ]
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    @property
    def total_quantity(self):
        """Total stock including shop and field"""
        return self.quantity_in_stock + self.quantity_in_field
    
    @property
    def is_low_stock(self):
        """Check if stock is below reorder level"""
        return self.quantity_in_stock <= self.reorder_level
    
    @property
    def stock_value(self):
        """Calculate total inventory value"""
        return self.total_quantity * self.cost_price


class InventoryMovement(TimeStampedModel):
    """
    Append-only ledger of all inventory movements
    NEVER UPDATE OR DELETE - only INSERT
    """
    PURCHASE = 'purchase'
    SALE = 'sale'
    TRANSFER_TO_AGENT = 'transfer_to_agent'
    RETURN_FROM_AGENT = 'return_from_agent'
    ADJUSTMENT = 'adjustment'
    REVERSAL = 'reversal'
    
    MOVEMENT_TYPES = [
        (PURCHASE, 'Purchase'),
        (SALE, 'Sale'),
        (TRANSFER_TO_AGENT, 'Transfer to Agent'),
        (RETURN_FROM_AGENT, 'Return from Agent'),
        (ADJUSTMENT, 'Stock Adjustment'),
        (REVERSAL, 'Reversal/Correction'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='movements')
    movement_type = models.CharField(max_length=30, choices=MOVEMENT_TYPES)
    quantity_delta = models.IntegerField(help_text='Positive for addition, negative for deduction')
    
    # Location tracking
    from_location = models.CharField(max_length=20, default='shop', help_text='shop or agent_id')
    to_location = models.CharField(max_length=20, default='shop', help_text='shop or agent_id')
    
    # Reference to related transaction
    reference_id = models.CharField(max_length=100, blank=True, help_text='Transaction or agent transfer ID')
    
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
        related_name='approved_reversals'
    )
    
    # Tracking
    performed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='inventory_movements')
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'inventory_movements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', '-created_at']),
            models.Index(fields=['movement_type']),
            models.Index(fields=['reference_id']),
        ]
    
    def __str__(self):
        return f"{self.movement_type}: {self.product.sku} ({self.quantity_delta:+d})"
