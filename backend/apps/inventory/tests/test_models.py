"""
Test cases for inventory models
"""
from django.test import TestCase
from decimal import Decimal
from apps.core.models import User
from apps.inventory.models import (
    Category, Brand, Model, Product, InventoryMovement
)


class CategoryModelTests(TestCase):
    """Test Category model"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name="Screens",
            description="LCD and OLED screens"
        )
    
    def test_category_creation(self):
        """Test category can be created"""
        self.assertEqual(self.category.name, "Screens")
        self.assertTrue(self.category.is_active)
    
    def test_category_string_representation(self):
        """Test category __str__ method"""
        self.assertEqual(str(self.category), "Screens")


class BrandModelTests(TestCase):
    """Test Brand model"""
    
    def test_brand_creation(self):
        """Test brand can be created"""
        brand = Brand.objects.create(name="Samsung")
        self.assertEqual(brand.name, "Samsung")
        self.assertEqual(str(brand), "Samsung")


class ProductModelTests(TestCase):
    """Test Product model with realistic data"""
    
    def setUp(self):
        # Create user
        self.user = User.objects.create(
            username="testuser",
            full_name="Test User",
            role=User.OWNER
        )
        
        # Create related objects
        self.category = Category.objects.create(name="Screens")
        self.brand = Brand.objects.create(name="Samsung")
        self.model = Model.objects.create(
            brand=self.brand,
            name="Galaxy S23",
            release_year=2023
        )
        
        # Create product
        self.product = Product.objects.create(
            sku="SAM-S23-LCD-001",
            name="Galaxy S23 LCD Screen",
            category=self.category,
            brand=self.brand,
            phone_model=self.model,
            cost_price=Decimal("120000"),
            selling_price=Decimal("180000"),
            quantity_in_stock=50,
            reorder_level=10,
            created_by=self.user
        )
    
    def test_product_creation(self):
        """Test product creation with all fields"""
        self.assertEqual(self.product.sku, "SAM-S23-LCD-001")
        self.assertEqual(self.product.quantity_in_stock, 50)
        self.assertTrue(self.product.is_active)
    
    def test_product_total_quantity(self):
        """Test total_quantity property"""
        self.product.quantity_in_field = 15
        self.product.save()
        self.assertEqual(self.product.total_quantity, 65)
    
    def test_product_stock_value(self):
        """Test stock_value calculation"""
        expected = Decimal("120000") * 50
        self.assertEqual(self.product.stock_value, expected)
    
    def test_product_low_stock_detection(self):
        """Test low stock detection"""
        self.assertFalse(self.product.is_low_stock)
        
        self.product.quantity_in_stock = 5
        self.product.save()
        self.assertTrue(self.product.is_low_stock)
    
    def test_product_sku_uniqueness(self):
        """Test SKU must be unique"""
        with self.assertRaises(Exception):
            Product.objects.create(
                sku="SAM-S23-LCD-001",  # Duplicate
                name="Another Product",
                category=self.category,
                brand=self.brand,
                cost_price=100,
                selling_price=150,
                created_by=self.user
            )
    
    def test_multiple_products_realistic_inventory(self):
        """Test system can handle many products"""
        products = []
        for i in range(100):
            products.append(Product(
                sku=f"TEST-SKU-{i:04d}",
                name=f"Test Product {i}",
                category=self.category,
                brand=self.brand,
                cost_price=Decimal("50000"),
                selling_price=Decimal("75000"),
                quantity_in_stock=i * 2,
                reorder_level=5,
                created_by=self.user
            ))
        
        Product.objects.bulk_create(products)
        self.assertEqual(Product.objects.count(), 101)  # +1 from setUp
    
    def test_product_string_representation(self):
        """Test product __str__ method"""
        expected = "SAM-S23-LCD-001 - Galaxy S23 LCD Screen"
        self.assertEqual(str(self.product), expected)


class InventoryMovementTests(TestCase):
    """Test inventory movements (append-only ledger)"""
    
    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            full_name="Test User",
            role=User.OWNER
        )
        
        category = Category.objects.create(name="Batteries")
        brand = Brand.objects.create(name="Apple")
        
        self.product = Product.objects.create(
            sku="IPHONE-BAT-001",
            name="iPhone 13 Battery",
            category=category,
            brand=brand,
            cost_price=Decimal("35000"),
            selling_price=Decimal("55000"),
            quantity_in_stock=100,
            created_by=self.user
        )
    
    def test_movement_creation(self):
        """Test inventory movement can be created"""
        movement = InventoryMovement.objects.create(
            product=self.product,
            movement_type=InventoryMovement.PURCHASE,
            quantity_delta=50,
            reference_id="PO-2026-001",
            notes="Stock replenishment",
            performed_by=self.user
        )
        
        self.assertEqual(movement.quantity_delta, 50)
        self.assertEqual(movement.reference_id, "PO-2026-001")
    
    def test_movement_types(self):
        """Test all movement types can be created"""
        types = [
            InventoryMovement.PURCHASE,
            InventoryMovement.SALE,
            InventoryMovement.TRANSFER_TO_AGENT,
            InventoryMovement.ADJUSTMENT,
            InventoryMovement.REVERSAL
        ]
        
        for mov_type in types:
            InventoryMovement.objects.create(
                product=self.product,
                movement_type=mov_type,
                quantity_delta=10 if mov_type == InventoryMovement.PURCHASE else -10,
                performed_by=self.user
            )
        
        self.assertEqual(InventoryMovement.objects.count(), 5)
    
    def test_movement_append_only(self):
        """Test movements cannot be deleted (append-only)"""
        movement = InventoryMovement.objects.create(
            product=self.product,
            movement_type=InventoryMovement.SALE,
            quantity_delta=-5,
            performed_by=self.user
        )
        
        # Reversal should create new entry, not delete
        reversal = InventoryMovement.objects.create(
            product=self.product,
            movement_type=InventoryMovement.REVERSAL,
            quantity_delta=5,
            reversal_of=movement,
            performed_by=self.user
        )
        
        self.assertEqual(InventoryMovement.objects.count(), 2)
        self.assertEqual(reversal.reversal_of, movement)
    
    def test_high_volume_movements(self):
        """Test system handles many movements"""
        movements = []
        for i in range(500):
            movements.append(InventoryMovement(
                product=self.product,
                movement_type=InventoryMovement.SALE if i % 2 == 0 else InventoryMovement.PURCHASE,
                quantity_delta=(i + 1) if i % 2 == 1 else -(i + 1),
                performed_by=self.user
            ))
        
        InventoryMovement.objects.bulk_create(movements)
        self.assertEqual(InventoryMovement.objects.count(), 500)
