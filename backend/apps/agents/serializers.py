"""
Serializers for agents module
"""
from rest_framework import serializers
from .models import Agent, AgentLedger, AgentPayment
from apps.inventory.serializers import ProductListSerializer


class AgentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for agent lists"""
    total_debt = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    can_take_more_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Agent
        fields = [
            'id', 'full_name', 'phone_number', 'business_name', 'area',
            'credit_limit', 'total_debt', 'can_take_more_stock', 'is_active', 'is_trusted'
        ]


class AgentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single agent"""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    total_debt = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    can_take_more_stock = serializers.BooleanField(read_only=True)
    debt_by_age = serializers.SerializerMethodField()
    
    class Meta:
        model = Agent
        fields = [
            'id', 'full_name', 'phone_number', 'id_number', 'address', 'area',
            'business_name', 'credit_limit', 'total_debt', 'can_take_more_stock',
            'debt_by_age', 'is_active', 'is_trusted', 'notes',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_debt_by_age(self, obj):
        return obj.get_debt_by_age()


class AgentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating agents"""
    
    class Meta:
        model = Agent
        fields = [
            'full_name', 'phone_number', 'id_number', 'address', 'area',
            'business_name', 'credit_limit', 'is_active', 'is_trusted', 'notes'
        ]


class AgentLedgerSerializer(serializers.ModelSerializer):
    """Serializer for agent ledger entries"""
    agent_name = serializers.CharField(source='agent.full_name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    transferred_by_name = serializers.CharField(source='transferred_by.full_name', read_only=True)
    remaining_debt = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    days_outstanding = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = AgentLedger
        fields = [
            'id', 'agent', 'agent_name', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'debt_amount', 'remaining_debt',
            'transfer_date', 'is_paid', 'paid_amount', 'payment_date',
            'days_outstanding', 'inventory_movement_id',
            'transferred_by', 'transferred_by_name', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'transferred_by', 'transfer_date']


class StockTransferSerializer(serializers.Serializer):
    """Serializer for transferring stock to agent"""
    agent_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        from apps.inventory.models import Product
        from .models import Agent
        
        # Validate agent exists and is active
        try:
            agent = Agent.objects.get(id=data['agent_id'], is_active=True)
        except Agent.DoesNotExist:
            raise serializers.ValidationError({'agent_id': 'Agent not found or inactive'})
        
        # Validate product exists and has enough stock
        try:
            product = Product.objects.get(id=data['product_id'], is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError({'product_id': 'Product not found or inactive'})
        
        if product.quantity_in_stock < data['quantity']:
            raise serializers.ValidationError({
                'quantity': f'Insufficient stock. Available: {product.quantity_in_stock}'
            })
        
        # Check agent credit limit
        debt_amount = data['quantity'] * data['unit_price']
        if not agent.can_take_more_stock:
            if agent.credit_limit > 0 and (agent.total_debt + debt_amount) > agent.credit_limit:
                raise serializers.ValidationError({
                    'agent_id': f'Credit limit exceeded. Current debt: {agent.total_debt}, Limit: {agent.credit_limit}'
                })
        
        data['agent'] = agent
        data['product'] = product
        data['debt_amount'] = debt_amount
        
        return data


class AgentPaymentSerializer(serializers.ModelSerializer):
    """Serializer for agent payments"""
    agent_name = serializers.CharField(source='agent.full_name', read_only=True)
    received_by_name = serializers.CharField(source='received_by.full_name', read_only=True)
    
    class Meta:
        model = AgentPayment
        fields = [
            'id', 'agent', 'agent_name', 'amount', 'payment_method',
            'reference_number', 'received_by', 'received_by_name',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'received_by']


class RecordPaymentSerializer(serializers.Serializer):
    """Serializer for recording agent payment"""
    agent_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    payment_method = serializers.ChoiceField(choices=['cash', 'mobile_money', 'bank_transfer'])
    reference_number = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    ledger_entries = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text='Optional: specific ledger entry IDs to apply payment to'
    )
