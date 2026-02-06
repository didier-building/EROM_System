"""
Integration tests for realistic shop scenarios
"""
from django.test import TestCase
from django.db import models
from django.db.models import F, Sum
from decimal import Decimal
from apps.core.test_factories import TestDataFactory
from apps.inventory.models import Product
from apps.agents.models import Agent


class RealisticShopTests(TestCase):
    """Test system with realistic shop data volume"""
    
    def setUp(self):
        """Create full shop with realistic data"""
        self.shop_data = TestDataFactory.setup_full_test_shop()
    
    def test_shop_creation_with_full_inventory(self):
        """Test system handles complete shop setup"""
        self.assertIsNotNone(self.shop_data['shop'])
        self.assertEqual(self.shop_data['shop'].name, "Aguka Electronics Test Shop")
    
    def test_realistic_product_count(self):
        """Test system created realistic number of products"""
        count = Product.objects.count()
        self.assertGreater(count, 50, "Should have at least 50 products")
        self.assertLess(count, 500, "Should have less than 500 products")
        print(f"\n✓ System handles {count} products")
    
    def test_multiple_brands_and_models(self):
        """Test system handles multiple brands and models"""
        brands_count = len(self.shop_data['brands'])
        self.assertGreaterEqual(brands_count, 6, "Should have at least 6 brands")
        print(f"\n✓ System handles {brands_count} brands")
    
    def test_multiple_agents(self):
        """Test system handles multiple field agents"""
        agents_count = Agent.objects.count()
        self.assertEqual(agents_count, 10)
        print(f"\n✓ System handles {agents_count} agents")
    
    def test_product_search_performance(self):
        """Test product search works with many products"""
        # Search for Samsung products
        samsung_products = Product.objects.filter(brand__name="Samsung")
        self.assertGreater(samsung_products.count(), 0)
        
        # Search for screens
        screens = Product.objects.filter(category__name__icontains="Screen")
        self.assertGreater(screens.count(), 0)
        
        print(f"\n✓ Found {samsung_products.count()} Samsung products")
        print(f"✓ Found {screens.count()} screen products")
    
    def test_low_stock_detection_at_scale(self):
        """Test low stock detection works with many products"""
        # Set some products to low stock
        products = Product.objects.all()[:5]
        for product in products:
            product.quantity_in_stock = 3
            product.reorder_level = 10
            product.save()
        
        low_stock_products = Product.objects.filter(
            quantity_in_stock__lte=F('reorder_level')
        )
        self.assertGreaterEqual(low_stock_products.count(), 5)
    
    def test_inventory_value_calculation(self):
        """Test system can calculate total inventory value"""
        total_value = Product.objects.aggregate(
            total=Sum(F('cost_price') * F('quantity_in_stock'))
        )['total'] or Decimal('0')
        
        self.assertGreater(total_value, 0)
        print(f"\n✓ Total inventory value: {total_value:,.0f} RWF")
    
    def test_agent_credit_limits(self):
        """Test agent credit management at scale"""
        agents = Agent.objects.all()
        
        for agent in agents:
            self.assertGreater(agent.credit_limit, 0)
            self.assertEqual(agent.total_debt, Decimal('0'))
            self.assertTrue(agent.can_take_more_stock)
    
    def test_category_distribution(self):
        """Test products are distributed across categories"""
        from apps.inventory.models import Category
        from django.db.models import Count
        
        categories_with_counts = Category.objects.annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0)
        
        self.assertGreater(categories_with_counts.count(), 3)
        print(f"\n✓ {categories_with_counts.count()} categories with products")
    
    def test_realistic_pricing(self):
        """Test products have realistic Rwanda market prices"""
        products = Product.objects.all()
        
        for product in products[:10]:
            # Check markup is reasonable (usually 30-70%)
            markup = (product.selling_price / product.cost_price - 1) * 100
            self.assertGreater(markup, 20, f"{product.name} markup too low")
            self.assertLess(markup, 100, f"{product.name} markup too high")
            
            # Check prices are in reasonable range for Rwanda market
            self.assertGreater(product.selling_price, Decimal('1000'))
            self.assertLess(product.selling_price, Decimal('500000'))


class PerformanceTests(TestCase):
    """Test system performance with high data volume"""
    
    def setUp(self):
        self.shop_data = TestDataFactory.setup_full_test_shop()
    
    def test_bulk_product_query_performance(self):
        """Test querying many products is efficient"""
        import time
        
        start = time.time()
        products = list(Product.objects.select_related(
            'category', 'brand', 'phone_model'
        ).all())
        end = time.time()
        
        query_time = end - start
        print(f"\n✓ Queried {len(products)} products in {query_time:.3f} seconds")
        self.assertLess(query_time, 1.0, "Query should take less than 1 second")
    
    def test_filtered_search_performance(self):
        """Test filtered searches are fast"""
        import time
        
        start = time.time()
        results = list(Product.objects.filter(
            category__name__icontains="Battery",
            brand__name="Samsung",
            is_active=True
        ))
        end = time.time()
        
        query_time = end - start
        print(f"\n✓ Filtered search returned {len(results)} results in {query_time:.3f}s")
        self.assertLess(query_time, 0.5)
