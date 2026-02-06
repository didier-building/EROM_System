"""
Serializers for sales module
"""
from rest_framework import serializers
from .models import Transaction, TransactionItem, Reconciliation, ReconciliationItem
from apps.inventory.serializers import ProductListSerializer


class TransactionItemSerializer(serializers.ModelSerializer):
    """Serializer for transaction line items"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = TransactionItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'discount', 'line_total'
        ]
        read_only_fields = ['id', 'line_total']


class TransactionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for transaction lists"""
    processed_by_name = serializers.CharField(source='processed_by.full_name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'transaction_type', 'transaction_date',
            'total_amount', 'payment_method', 'processed_by', 'processed_by_name'
        ]


class TransactionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single transaction"""
    items = TransactionItemSerializer(many=True, read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.full_name', read_only=True)
    reversal_approved_by_name = serializers.CharField(source='reversal_approved_by.full_name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'transaction_type', 'transaction_date',
            'subtotal', 'tax_amount', 'discount_amount', 'total_amount',
            'payment_method', 'amount_paid', 'change_given',
            'customer_name', 'customer_phone',
            'reversal_of', 'reversal_reason', 'reversal_approved_by', 'reversal_approved_by_name',
            'processed_by', 'processed_by_name', 'notes', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at', 'updated_at', 'processed_by']


class SaleItemInput(serializers.Serializer):
    """Input serializer for sale items"""
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, default=0)


class CreateSaleSerializer(serializers.Serializer):
    """Serializer for creating a sale transaction"""
    items = serializers.ListField(
        child=SaleItemInput(),
        min_length=1
    )
    payment_method = serializers.ChoiceField(
        choices=['cash', 'mobile_money', 'bank_transfer', 'credit']
    )
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    customer_name = serializers.CharField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        from apps.inventory.models import Product
        
        # Validate all products exist and have sufficient stock
        items = data['items']
        for item in items:
            try:
                product = Product.objects.get(id=item['product_id'], is_active=True)
                if product.quantity_in_stock < item['quantity']:
                    raise serializers.ValidationError({
                        'items': f'Insufficient stock for {product.name}. Available: {product.quantity_in_stock}'
                    })
                item['product'] = product
            except Product.DoesNotExist:
                raise serializers.ValidationError({
                    'items': f'Product with ID {item["product_id"]} not found or inactive'
                })
        
        # Calculate totals
        subtotal = sum(
            (item['quantity'] * item['unit_price']) - item.get('discount', 0)
            for item in items
        )
        
        # Validate payment
        if data['amount_paid'] < subtotal:
            raise serializers.ValidationError({
                'amount_paid': f'Payment insufficient. Total: {subtotal}, Paid: {data["amount_paid"]}'
            })
        
        data['subtotal'] = subtotal
        data['change_given'] = data['amount_paid'] - subtotal
        
        return data


class ReconciliationItemSerializer(serializers.ModelSerializer):
    """Serializer for reconciliation items"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = ReconciliationItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'system_count', 'physical_count', 'variance',
            'has_discrepancy', 'discrepancy_reason',
            'correction_approved', 'correction_created'
        ]
        read_only_fields = ['id', 'variance', 'has_discrepancy']


class ReconciliationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for reconciliation lists"""
    performed_by_name = serializers.CharField(source='performed_by.full_name', read_only=True)
    total_discrepancies = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Reconciliation
        fields = [
            'id', 'reconciliation_date', 'reconciliation_type', 'status',
            'total_discrepancies', 'performed_by', 'performed_by_name'
        ]


class ReconciliationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single reconciliation"""
    items = ReconciliationItemSerializer(many=True, read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True)
    total_discrepancies = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Reconciliation
        fields = [
            'id', 'reconciliation_date', 'reconciliation_type', 'status',
            'total_discrepancies', 'performed_by', 'performed_by_name',
            'approved_by', 'approved_by_name', 'notes', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'performed_by']


class ReconciliationCountInput(serializers.Serializer):
    """Input for blind count entry"""
    product_id = serializers.IntegerField()
    physical_count = serializers.IntegerField(min_value=0)
    discrepancy_reason = serializers.CharField(required=False, allow_blank=True)
