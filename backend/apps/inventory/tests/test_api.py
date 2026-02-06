"""
API tests for inventory endpoints
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from apps.core.models import User, Shop
from apps.inventory.models import Category, Brand, Model, Product


class InventoryAPITests(TestCase):
    """Test inventory API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create shop
        self.shop = Shop.objects.create(
            name="Test Shop",
            owner_name="Owner",
            phone_number="+250788123456",
            license_key="TEST-KEY",
            device_id="test-device"
        )
        
        # Create users
        self.owner = User.objects.create(
            username="owner",
            full_name="Owner",
            role=User.OWNER,
            is_active=True
        )
        self.owner.set_password("pass123")
        self.owner.save()
        
        self.cashier = User.objects.create(
            username="cashier",
            full_name="Cashier",
            role=User.CASHIER,
            is_active=True
        )
        self.cashier.set_password("pass123")
        self.cashier.save()
        
        # Authenticate as owner
        self.token = self.owner.generate_session_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        
        # Create test data
        self.category = Category.objects.create(name="Test Category")
        self.brand = Brand.objects.create(name="Test Brand")
        self.model = Model.objects.create(
            brand=self.brand,
            name="Test Model",
            release_year=2023
        )
        
        self.product = Product.objects.create(
            sku="TEST-001",
            name="Test Product",
            category=self.category,
            brand=self.brand,
            phone_model=self.model,
            cost_price=Decimal("50000"),
            selling_price=Decimal("75000"),
            quantity_in_stock=100,
            reorder_level=10,
            created_by=self.owner
        )
    
    def test_list_products(self):
        """Test listing products"""
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['sku'], 'TEST-001')
    
    def test_create_product(self):
        """Test creating new product"""
        url = reverse('product-list')
        data = {
            'sku': 'NEW-PRODUCT-001',
            'name': 'New Test Product',
            'category': self.category.id,
            'brand': self.brand.id,
            'phone_model': self.model.id,
            'cost_price': '60000',
            'selling_price': '90000',
            'quantity_in_stock': 50,
            'reorder_level': 5
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
    
    def test_update_product(self):
        """Test updating product"""
        url = reverse('product-detail', args=[self.product.id])
        data = {
            'sku': 'TEST-001',
            'name': 'Updated Product Name',
            'category': self.category.id,
            'brand': self.brand.id,
            'cost_price': '55000',
            'selling_price': '80000',
            'quantity_in_stock': 100,
            'reorder_level': 10
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Product Name')
    
    def test_low_stock_filter(self):
        """Test low stock filtering"""
        # Create low stock product
        Product.objects.create(
            sku="LOW-STOCK-001",
            name="Low Stock Item",
            category=self.category,
            brand=self.brand,
            cost_price=Decimal("30000"),
            selling_price=Decimal("45000"),
            quantity_in_stock=3,
            reorder_level=10,
            created_by=self.owner
        )
        
        url = reverse('product-low-stock')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sku'], 'LOW-STOCK-001')
    
    def test_adjust_stock_owner_only(self):
        """Test stock adjustment requires owner permission"""
        url = reverse('product-adjust-stock', args=[self.product.id])
        data = {
            'quantity': 10,
            'reason': 'Damaged items removed'
        }
        
        # Owner can adjust
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Cashier cannot adjust
        cashier_token = self.cashier.generate_session_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {cashier_token}')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_categories(self):
        """Test listing categories"""
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['count'], 0)
    
    def test_search_products_by_name(self):
        """Test product search functionality"""
        url = reverse('product-list')
        response = self.client.get(url, {'search': 'Test Product'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_filter_products_by_category(self):
        """Test filtering products by category"""
        url = reverse('product-list')
        response = self.client.get(url, {'category': self.category.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_handle_large_inventory(self):
        """Test system handles large number of products"""
        # Create 200 products
        products = []
        for i in range(200):
            products.append(Product(
                sku=f"BULK-{i:04d}",
                name=f"Bulk Product {i}",
                category=self.category,
                brand=self.brand,
                cost_price=Decimal("50000"),
                selling_price=Decimal("75000"),
                quantity_in_stock=50,
                reorder_level=5,
                created_by=self.owner
            ))
        
        Product.objects.bulk_create(products)
        
        # Test API handles large dataset
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 201)
        self.assertIsNotNone(response.data.get('next'))  # Pagination
