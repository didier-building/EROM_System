"""
Serializers for inventory module
"""
from rest_framework import serializers
from .models import Category, Brand, Model, Product, InventoryMovement


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories"""
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'subcategories', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return CategorySerializer(obj.subcategories.filter(is_active=True), many=True).data
        return []


class BrandSerializer(serializers.ModelSerializer):
    """Serializer for smartphone brands"""
    class Meta:
        model = Brand
        fields = ['id', 'name', 'logo', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModelSerializer(serializers.ModelSerializer):
    """Serializer for smartphone models"""
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    
    class Meta:
        model = Model
        fields = ['id', 'brand', 'brand_name', 'name', 'model_number', 'release_year', 'image', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'category', 'category_name', 'brand', 'brand_name',
            'quantity_in_stock', 'quantity_in_field', 'selling_price', 'reorder_level', 
            'is_active', 'is_low_stock'
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single product"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    phone_model_name = serializers.CharField(source='phone_model.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)
    stock_value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'description', 'category', 'category_name',
            'brand', 'brand_name', 'phone_model', 'phone_model_name',
            'quantity_in_stock', 'quantity_in_field', 'total_quantity', 'reorder_level',
            'cost_price', 'selling_price', 'stock_value', 'image', 'barcode',
            'is_active', 'is_low_stock', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products"""
    
    class Meta:
        model = Product
        fields = [
            'sku', 'name', 'description', 'category', 'brand', 'phone_model',
            'quantity_in_stock', 'reorder_level', 'cost_price', 'selling_price',
            'image', 'barcode', 'is_active'
        ]
    
    def validate_sku(self, value):
        """Ensure SKU is unique"""
        instance = self.instance
        if Product.objects.filter(sku=value).exclude(pk=instance.pk if instance else None).exists():
            raise serializers.ValidationError("Product with this SKU already exists")
        return value
    
    def validate(self, data):
        """Validate pricing"""
        cost_price = data.get('cost_price', 0)
        selling_price = data.get('selling_price', 0)
        
        if selling_price < cost_price:
            raise serializers.ValidationError({
                'selling_price': 'Selling price cannot be less than cost price'
            })
        
        return data


class InventoryMovementSerializer(serializers.ModelSerializer):
    """Serializer for inventory movements"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.full_name', read_only=True)
    reversal_approved_by_name = serializers.CharField(source='reversal_approved_by.full_name', read_only=True)
    
    class Meta:
        model = InventoryMovement
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'movement_type',
            'quantity_delta', 'from_location', 'to_location', 'reference_id',
            'reversal_of', 'reversal_reason', 'reversal_approved_by', 'reversal_approved_by_name',
            'performed_by', 'performed_by_name', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'performed_by']


class StockAdjustmentSerializer(serializers.Serializer):
    """Serializer for manual stock adjustments"""
    product_id = serializers.IntegerField()
    quantity_delta = serializers.IntegerField()
    reason = serializers.CharField()
    
    def validate_quantity_delta(self, value):
        if value == 0:
            raise serializers.ValidationError("Quantity delta cannot be zero")
        return value
