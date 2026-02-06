"""
Views for sales and POS
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.utils import timezone

from apps.core.permissions import IsCashierOrOwner, IsOwner
from apps.inventory.models import Product, InventoryMovement
from .models import Transaction, TransactionItem, Reconciliation, ReconciliationItem
from .serializers import (
    TransactionListSerializer, TransactionDetailSerializer, CreateSaleSerializer,
    ReconciliationListSerializer, ReconciliationDetailSerializer,
    ReconciliationItemSerializer, ReconciliationCountInput
)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for transactions (read-only - transactions created via create_sale action)
    """
    queryset = Transaction.objects.select_related('processed_by', 'reversal_approved_by').prefetch_related('items').all()
    permission_classes = [IsCashierOrOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'payment_method', 'processed_by']
    ordering_fields = ['transaction_date', 'total_amount']
    ordering = ['-transaction_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TransactionListSerializer
        return TransactionDetailSerializer
    
    @action(detail=False, methods=['post'])
    def create_sale(self, request):
        """Create a new sale transaction"""
        serializer = CreateSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        with transaction.atomic():
            # Create transaction
            txn = Transaction.objects.create(
                transaction_type=Transaction.SALE,
                subtotal=data['subtotal'],
                total_amount=data['subtotal'],
                payment_method=data['payment_method'],
                amount_paid=data['amount_paid'],
                change_given=data['change_given'],
                customer_name=data.get('customer_name', ''),
                customer_phone=data.get('customer_phone', ''),
                processed_by=request.user,
                notes=data.get('notes', '')
            )
            
            # Create transaction items and update inventory
            for item_data in data['items']:
                product = item_data['product']
                quantity = item_data['quantity']
                unit_price = item_data['unit_price']
                discount = item_data.get('discount', 0)
                
                # Create transaction item
                TransactionItem.objects.create(
                    transaction=txn,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount=discount
                )
                
                # Create inventory movement
                InventoryMovement.objects.create(
                    product=product,
                    movement_type=InventoryMovement.SALE,
                    quantity_delta=-quantity,
                    from_location='shop',
                    to_location='customer',
                    reference_id=txn.transaction_id,
                    performed_by=request.user,
                    notes=f'Sale: {txn.transaction_id}'
                )
                
                # Update product stock
                product.quantity_in_stock -= quantity
                product.save(update_fields=['quantity_in_stock', 'updated_at'])
        
        return Response({
            'success': True,
            'message': 'Sale created successfully',
            'data': TransactionDetailSerializer(txn).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get daily sales summary"""
        date = request.query_params.get('date', timezone.now().date())
        
        transactions = self.get_queryset().filter(
            transaction_type=Transaction.SALE,
            transaction_date__date=date
        )
        
        total_sales = sum(t.total_amount for t in transactions)
        total_transactions = transactions.count()
        
        by_payment_method = {}
        for txn in transactions:
            method = txn.payment_method
            by_payment_method[method] = by_payment_method.get(method, 0) + float(txn.total_amount)
        
        return Response({
            'success': True,
            'data': {
                'date': date,
                'total_sales': float(total_sales),
                'total_transactions': total_transactions,
                'by_payment_method': by_payment_method,
                'transactions': TransactionListSerializer(transactions, many=True).data
            }
        })


class ReconciliationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for stock reconciliations
    """
    queryset = Reconciliation.objects.select_related('performed_by', 'approved_by').prefetch_related('items').all()
    permission_classes = [IsCashierOrOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'reconciliation_type', 'performed_by']
    ordering_fields = ['reconciliation_date']
    ordering = ['-reconciliation_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ReconciliationListSerializer
        return ReconciliationDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Start a new reconciliation"""
        reconciliation_type = request.data.get('reconciliation_type', 'daily')
        
        reconciliation = Reconciliation.objects.create(
            reconciliation_type=reconciliation_type,
            status='in_progress',
            performed_by=request.user
        )
        
        return Response({
            'success': True,
            'message': 'Reconciliation started',
            'data': ReconciliationDetailSerializer(reconciliation).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def add_count(self, request, pk=None):
        """Add product count to reconciliation"""
        reconciliation = self.get_object()
        
        if reconciliation.status != 'in_progress':
            return Response(
                {'success': False, 'error': 'Reconciliation is not in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReconciliationCountInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product_id = serializer.validated_data['product_id']
        physical_count = serializer.validated_data['physical_count']
        discrepancy_reason = serializer.validated_data.get('discrepancy_reason', '')
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Product not found or inactive'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create or update reconciliation item
        item, created = ReconciliationItem.objects.update_or_create(
            reconciliation=reconciliation,
            product=product,
            defaults={
                'system_count': product.quantity_in_stock,
                'physical_count': physical_count,
                'discrepancy_reason': discrepancy_reason
            }
        )
        
        return Response({
            'success': True,
            'message': 'Count recorded',
            'data': ReconciliationItemSerializer(item).data
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark reconciliation as completed"""
        reconciliation = self.get_object()
        
        if reconciliation.status != 'in_progress':
            return Response(
                {'success': False, 'error': 'Reconciliation is not in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reconciliation.status = 'completed'
        reconciliation.save(update_fields=['status', 'updated_at'])
        
        return Response({
            'success': True,
            'message': 'Reconciliation completed',
            'data': ReconciliationDetailSerializer(reconciliation).data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def approve(self, request, pk=None):
        """Approve reconciliation (Owner only)"""
        reconciliation = self.get_object()
        
        if reconciliation.status != 'completed':
            return Response(
                {'success': False, 'error': 'Reconciliation must be completed first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reconciliation.status = 'approved'
        reconciliation.approved_by = request.user
        reconciliation.save(update_fields=['status', 'approved_by', 'updated_at'])
        
        return Response({
            'success': True,
            'message': 'Reconciliation approved',
            'data': ReconciliationDetailSerializer(reconciliation).data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def create_corrections(self, request, pk=None):
        """Create inventory corrections for discrepancies (Owner only)"""
        reconciliation = self.get_object()
        
        if reconciliation.status != 'approved':
            return Response(
                {'success': False, 'error': 'Reconciliation must be approved first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        discrepancies = reconciliation.items.filter(has_discrepancy=True, correction_created=False)
        
        with transaction.atomic():
            corrections_created = 0
            
            for item in discrepancies:
                # Create inventory movement for correction
                InventoryMovement.objects.create(
                    product=item.product,
                    movement_type=InventoryMovement.ADJUSTMENT,
                    quantity_delta=item.variance,
                    from_location='shop',
                    to_location='shop',
                    reference_id=f'RECON_{reconciliation.id}',
                    performed_by=request.user,
                    reversal_approved_by=request.user,
                    notes=f'Reconciliation correction: {item.discrepancy_reason}'
                )
                
                # Update product stock
                product = item.product
                product.quantity_in_stock += item.variance
                product.save(update_fields=['quantity_in_stock', 'updated_at'])
                
                # Mark correction as created
                item.correction_created = True
                item.correction_approved = True
                item.save(update_fields=['correction_created', 'correction_approved', 'updated_at'])
                
                corrections_created += 1
        
        return Response({
            'success': True,
            'message': f'{corrections_created} corrections created',
            'data': {
                'corrections_created': corrections_created
            }
        })
