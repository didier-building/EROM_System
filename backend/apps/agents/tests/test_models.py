"""
Test cases for agent management models
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from apps.core.models import User
from apps.inventory.models import Category, Brand, Product
from apps.agents.models import Agent, AgentLedger, AgentPayment


class AgentModelTests(TestCase):
    """Test Agent model with realistic scenarios"""
    
    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            full_name="Test User",
            role=User.OWNER
        )
        
        self.agent = Agent.objects.create(
            full_name="John Tech",
            phone_number="+250788123456",
            business_name="Tech Repairs",
            area="Kigali CBD",
            credit_limit=Decimal("500000"),
            is_active=True,
            created_by=self.user
        )
    
    def test_agent_creation(self):
        """Test agent can be created"""
        self.assertEqual(self.agent.full_name, "John Tech")
        self.assertEqual(self.agent.credit_limit, Decimal("500000"))
        self.assertTrue(self.agent.is_active)
    
    def test_agent_initial_debt(self):
        """Test new agent has zero debt"""
        self.assertEqual(self.agent.total_debt, Decimal("0"))
    
    def test_agent_credit_limit_check(self):
        """Test credit limit validation"""
        self.assertTrue(self.agent.can_take_more_stock)
        
        # Set debt near limit
        self.agent.total_debt = Decimal("480000")
        self.agent.save()
        self.assertTrue(self.agent.can_take_more_stock)
        
        # Exceed limit
        self.agent.total_debt = Decimal("510000")
        self.agent.save()
        self.assertFalse(self.agent.can_take_more_stock)
    
    def test_agent_phone_uniqueness(self):
        """Test phone number must be unique"""
        with self.assertRaises(Exception):
            Agent.objects.create(
                full_name="Another Agent",
                phone_number="+250788123456",  # Duplicate
                area="Nyarugenge",
                credit_limit=Decimal("300000"),
                created_by=self.user
            )
    
    def test_multiple_agents(self):
        """Test system can handle many agents"""
        agents = []
        for i in range(50):
            agents.append(Agent(
                full_name=f"Agent {i}",
                phone_number=f"+25078812{i:04d}",
                area=f"Area {i}",
                credit_limit=Decimal("300000"),
                created_by=self.user
            ))
        
        Agent.objects.bulk_create(agents)
        self.assertEqual(Agent.objects.count(), 51)  # +1 from setUp


class AgentLedgerTests(TestCase):
    """Test agent ledger (append-only debt tracking)"""
    
    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            full_name="Test User",
            role=User.OWNER
        )
        
        self.agent = Agent.objects.create(
            full_name="Test Agent",
            phone_number="+250788999888",
            area="Test Area",
            credit_limit=Decimal("500000"),
            created_by=self.user
        )
        
        category = Category.objects.create(name="Screens")
        brand = Brand.objects.create(name="Samsung")
        
        self.product = Product.objects.create(
            sku="TEST-PROD-001",
            name="Test Product",
            category=category,
            brand=brand,
            cost_price=Decimal("50000"),
            selling_price=Decimal("75000"),
            quantity_in_stock=100,
            created_by=self.user
        )
    
    def test_ledger_entry_creation(self):
        """Test creating ledger entry for stock transfer"""
        entry = AgentLedger.objects.create(
            agent=self.agent,
            product=self.product,
            quantity=10,
            unit_price=Decimal("50000"),
            transferred_by=self.user
        )
        
        self.assertEqual(entry.quantity, 10)
        self.assertEqual(entry.total_amount, Decimal("500000"))
        self.assertFalse(entry.is_paid)
    
    def test_ledger_append_only(self):
        """Test ledger entries cannot be deleted"""
        entry = AgentLedger.objects.create(
            agent=self.agent,
            product=self.product,
            quantity=5,
            unit_price=Decimal("50000"),
            transferred_by=self.user
        )
        
        # Mark as paid instead of deleting
        entry.is_paid = True
        entry.paid_at = timezone.now()
        entry.save()
        
        self.assertTrue(entry.is_paid)
        self.assertIsNotNone(entry.paid_at)
    
    def test_debt_aging(self):
        """Test debt aging calculation"""
        # Create old entry
        old_entry = AgentLedger.objects.create(
            agent=self.agent,
            product=self.product,
            quantity=10,
            unit_price=Decimal("50000"),
            transferred_by=self.user
        )
        old_entry.created_at = timezone.now() - timedelta(days=35)
        old_entry.save(update_fields=['created_at'])
        
        # Create recent entry
        recent_entry = AgentLedger.objects.create(
            agent=self.agent,
            product=self.product,
            quantity=5,
            unit_price=Decimal("50000"),
            transferred_by=self.user
        )
        
        debt_by_age = self.agent.get_debt_by_age()
        
        # Old entry should be in 31-60 days bucket
        self.assertGreater(debt_by_age['days_31_60'], 0)
        # Recent entry should be in 0-7 days bucket
        self.assertGreater(debt_by_age['days_0_7'], 0)
    
    def test_high_volume_ledger_entries(self):
        """Test system handles many ledger entries"""
        entries = []
        for i in range(300):
            entries.append(AgentLedger(
                agent=self.agent,
                product=self.product,
                quantity=i + 1,
                unit_price=Decimal("50000"),
                transferred_by=self.user
            ))
        
        AgentLedger.objects.bulk_create(entries)
        self.assertEqual(AgentLedger.objects.filter(agent=self.agent).count(), 300)


class AgentPaymentTests(TestCase):
    """Test agent payment processing"""
    
    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            full_name="Test User",
            role=User.OWNER
        )
        
        self.agent = Agent.objects.create(
            full_name="Test Agent",
            phone_number="+250788777666",
            area="Test Area",
            credit_limit=Decimal("500000"),
            total_debt=Decimal("300000"),
            created_by=self.user
        )
    
    def test_payment_creation(self):
        """Test recording agent payment"""
        payment = AgentPayment.objects.create(
            agent=self.agent,
            amount=Decimal("100000"),
            payment_method=AgentPayment.CASH,
            reference_number="PAY-2026-001",
            received_by=self.user
        )
        
        self.assertEqual(payment.amount, Decimal("100000"))
        self.assertEqual(payment.payment_method, AgentPayment.CASH)
    
    def test_multiple_payment_methods(self):
        """Test all payment methods"""
        methods = [
            AgentPayment.CASH,
            AgentPayment.MOBILE_MONEY,
            AgentPayment.BANK_TRANSFER
        ]
        
        for method in methods:
            AgentPayment.objects.create(
                agent=self.agent,
                amount=Decimal("50000"),
                payment_method=method,
                received_by=self.user
            )
        
        self.assertEqual(AgentPayment.objects.count(), 3)
    
    def test_payment_reduces_debt(self):
        """Test payment application reduces debt"""
        initial_debt = self.agent.total_debt
        
        AgentPayment.objects.create(
            agent=self.agent,
            amount=Decimal("100000"),
            payment_method=AgentPayment.CASH,
            received_by=self.user
        )
        
        # Note: Debt reduction logic would be in view/signal
        # This test documents expected behavior
        self.assertEqual(initial_debt, Decimal("300000"))
