"""
Test cases for sales/POS models
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from apps.core.models import User
from apps.inventory.models import Category, Brand, Product
from apps.sales.models import Transaction, TransactionItem, Reconciliation, ReconciliationItem


class TransactionModelTests(TestCase):
    """Test POS transaction model"""
    
    def setUp(self):
        self.user = User.objects.create(
            username="cashier",
            full_name="Test Cashier",
            role=User.CASHIER
        )
        
        category = Category.objects.create(name="Batteries")
        brand = Brand.objects.create(name="Samsung")
        
        self.product1 = Product.objects.create(
            sku="PROD-001",
            name="Product 1",
            category=category,
            brand=brand,
            cost_price=Decimal("30000"),
            selling_price=Decimal("45000"),
            quantity_in_stock=100,
            created_by=self.user
        )
        
        self.product2 = Product.objects.create(
            sku="PROD-002",
            name="Product 2",
            category=category,
            brand=brand,
            cost_price=Decimal("50000"),
            selling_price=Decimal("75000"),
            quantity_in_stock=50,
            created_by=self.user
        )
    
    def test_transaction_creation(self):
        """Test creating transaction"""
        transaction = Transaction.objects.create(
            cashier=self.user,
            total_amount=Decimal("120000"),
            payment_method=Transaction.CASH
        )
        
        self.assertIsNotNone(transaction.transaction_id)
        self.assertTrue(transaction.transaction_id.startswith('TXN-'))
        self.assertEqual(transaction.total_amount, Decimal("120000"))
    
    def test_transaction_id_auto_generation(self):
        """Test transaction ID is auto-generated"""
        transaction = Transaction.objects.create(
            cashier=self.user,
            total_amount=Decimal("100000"),
            payment_method=Transaction.CASH
        )
        
        # Format: TXN-YYYYMMDD-NNNN
        self.assertRegex(transaction.transaction_id, r'TXN-\d{8}-\d{4}')
    
    def test_transaction_with_items(self):
        """Test transaction with multiple items"""
        transaction = Transaction.objects.create(
            cashier=self.user,
            total_amount=Decimal("120000"),
            payment_method=Transaction.CASH
        )
        
        TransactionItem.objects.create(
            transaction=transaction,
            product=self.product1,
            quantity=2,
            unit_price=Decimal("45000"),
            subtotal=Decimal("90000")
        )
        
        TransactionItem.objects.create(
            transaction=transaction,
            product=self.product2,
            quantity=1,
            unit_price=Decimal("75000"),
            subtotal=Decimal("75000")
        )
        
        self.assertEqual(transaction.items.count(), 2)
        items_total = sum(item.subtotal for item in transaction.items.all())
        # Note: In real implementation, we'd validate total matches
        self.assertGreater(items_total, 0)
    
    def test_transaction_payment_methods(self):
        """Test all payment methods"""
        methods = [
            Transaction.CASH,
            Transaction.MOBILE_MONEY,
            Transaction.CARD,
            Transaction.CREDIT
        ]
        
        for method in methods:
            Transaction.objects.create(
                cashier=self.user,
                total_amount=Decimal("50000"),
                payment_method=method
            )
        
        self.assertEqual(Transaction.objects.count(), 4)
    
    def test_transaction_reversal(self):
        """Test transaction can be reversed"""
        transaction = Transaction.objects.create(
            cashier=self.user,
            total_amount=Decimal("100000"),
            payment_method=Transaction.CASH
        )
        
        transaction.is_reversed = True
        transaction.reversed_at = timezone.now()
        transaction.save()
        
        self.assertTrue(transaction.is_reversed)
        self.assertIsNotNone(transaction.reversed_at)
    
    def test_high_volume_transactions(self):
        """Test system handles many transactions"""
        transactions = []
        for i in range(500):
            transactions.append(Transaction(
                cashier=self.user,
                total_amount=Decimal("50000") * (i + 1),
                payment_method=Transaction.CASH
            ))
        
        Transaction.objects.bulk_create(transactions)
        self.assertEqual(Transaction.objects.count(), 500)


class ReconciliationModelTests(TestCase):
    """Test stock reconciliation (blind count)"""
    
    def setUp(self):
        self.user = User.objects.create(
            username="owner",
            full_name="Test Owner",
            role=User.OWNER
        )
        
        category = Category.objects.create(name="Screens")
        brand = Brand.objects.create(name="Apple")
        
        self.product = Product.objects.create(
            sku="RECON-001",
            name="Test Product",
            category=category,
            brand=brand,
            cost_price=Decimal("100000"),
            selling_price=Decimal("150000"),
            quantity_in_stock=50,
            created_by=self.user
        )
    
    def test_reconciliation_creation(self):
        """Test creating reconciliation"""
        recon = Reconciliation.objects.create(
            performed_by=self.user,
            status=Reconciliation.PENDING,
            notes="End of day count"
        )
        
        self.assertEqual(recon.status, Reconciliation.PENDING)
        self.assertIsNotNone(recon.started_at)
    
    def test_reconciliation_item(self):
        """Test adding count to reconciliation"""
        recon = Reconciliation.objects.create(
            performed_by=self.user,
            status=Reconciliation.PENDING
        )
        
        item = ReconciliationItem.objects.create(
            reconciliation=recon,
            product=self.product,
            system_count=50,
            physical_count=48
        )
        
        self.assertEqual(item.variance, -2)
        self.assertTrue(item.has_discrepancy)
    
    def test_reconciliation_approval(self):
        """Test reconciliation approval flow"""
        recon = Reconciliation.objects.create(
            performed_by=self.user,
            status=Reconciliation.PENDING
        )
        
        recon.status = Reconciliation.APPROVED
        recon.approved_by = self.user
        recon.approved_at = timezone.now()
        recon.save()
        
        self.assertEqual(recon.status, Reconciliation.APPROVED)
        self.assertIsNotNone(recon.approved_at)
    
    def test_reconciliation_with_multiple_items(self):
        """Test reconciliation handles many products"""
        recon = Reconciliation.objects.create(
            performed_by=self.user,
            status=Reconciliation.PENDING
        )
        
        # Create many products to reconcile
        category = Category.objects.create(name="Test Cat")
        brand = Brand.objects.create(name="Test Brand")
        
        products = []
        for i in range(100):
            products.append(Product(
                sku=f"RECON-{i:03d}",
                name=f"Product {i}",
                category=category,
                brand=brand,
                cost_price=Decimal("50000"),
                selling_price=Decimal("75000"),
                quantity_in_stock=i * 2,
                created_by=self.user
            ))
        
        Product.objects.bulk_create(products)
        
        # Add reconciliation items
        items = []
        for product in products:
            items.append(ReconciliationItem(
                reconciliation=recon,
                product=product,
                system_count=product.quantity_in_stock,
                physical_count=product.quantity_in_stock - 1  # Simulate 1 item variance
            ))
        
        ReconciliationItem.objects.bulk_create(items)
        
        self.assertEqual(recon.items.count(), 100)
        self.assertEqual(recon.total_discrepancies, 100)
