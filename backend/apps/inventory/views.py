"""
Views for inventory management
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from apps.core.permissions import IsCashierOrOwner, IsOwner, IsOwnerOrReadOnly
from .models import Category, Brand, Model, Product, InventoryMovement
from .serializers import (
    CategorySerializer, BrandSerializer, ModelSerializer,
    ProductListSerializer, ProductDetailSerializer, ProductCreateUpdateSerializer,
    InventoryMovementSerializer, StockAdjustmentSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for product categories
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsCashierOrOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only show active categories by default
        if self.request.query_params.get('show_inactive') != 'true':
            queryset = queryset.filter(is_active=True)
        return queryset
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get category tree (root categories with subcategories)"""
        root_categories = self.get_queryset().filter(parent=None)
        serializer = self.get_serializer(root_categories, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class BrandViewSet(viewsets.ModelViewSet):
    """
    ViewSet for smartphone brands
    """
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsCashierOrOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('show_inactive') != 'true':
            queryset = queryset.filter(is_active=True)
        return queryset


class ModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for smartphone models
    """
    queryset = Model.objects.select_related('brand').all()
    serializer_class = ModelSerializer
    permission_classes = [IsCashierOrOwner]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['name', 'model_number']
    filterset_fields = ['brand', 'is_active']
    ordering_fields = ['name', 'release_year', 'created_at']
    ordering = ['brand__name', 'name']
    
    @action(detail=False, methods=['get'])
    def by_brand(self, request):
        """Get models grouped by brand"""
        brand_id = request.query_params.get('brand_id')
        if not brand_id:
            return Response(
                {'success': False, 'error': 'brand_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        models = self.get_queryset().filter(brand_id=brand_id, is_active=True)
        serializer = self.get_serializer(models, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for products
    """
    queryset = Product.objects.select_related(
        'category', 'brand', 'phone_model', 'created_by'
    ).all()
    permission_classes = [IsCashierOrOwner]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['sku', 'name', 'description', 'barcode']
    filterset_fields = ['category', 'brand', 'phone_model', 'is_active']
    ordering_fields = ['name', 'sku', 'selling_price', 'quantity_in_stock', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock"""
        products = self.get_queryset().filter(
            quantity_in_stock__lte=models.F('reorder_level'),
            is_active=True
        )
        serializer = ProductListSerializer(products, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': products.count()
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced product search"""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({
                'success': True,
                'data': [],
                'message': 'No search query provided'
            })
        
        products = self.get_queryset().filter(
            Q(sku__icontains=query) |
            Q(name__icontains=query) |
            Q(barcode=query) |
            Q(description__icontains=query)
        ).filter(is_active=True)[:20]  # Limit to 20 results
        
        serializer = ProductListSerializer(products, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def adjust_stock(self, request, pk=None):
        """Manual stock adjustment (Owner only)"""
        product = self.get_object()
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        quantity_delta = serializer.validated_data['quantity_delta']
        reason = serializer.validated_data['reason']
        
        # Create inventory movement
        movement = InventoryMovement.objects.create(
            product=product,
            movement_type=InventoryMovement.ADJUSTMENT,
            quantity_delta=quantity_delta,
            from_location='shop',
            to_location='shop',
            performed_by=request.user,
            notes=reason
        )
        
        # Update product stock
        product.quantity_in_stock += quantity_delta
        product.save(update_fields=['quantity_in_stock', 'updated_at'])
        
        return Response({
            'success': True,
            'message': 'Stock adjusted successfully',
            'data': {
                'new_quantity': product.quantity_in_stock,
                'movement_id': movement.id
            }
        })


class InventoryMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for inventory movements (read-only)
    """
    queryset = InventoryMovement.objects.select_related(
        'product', 'performed_by', 'reversal_approved_by'
    ).all()
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsCashierOrOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'movement_type', 'performed_by']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Get movement history for a specific product"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'success': False, 'error': 'product_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        movements = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(movements, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
