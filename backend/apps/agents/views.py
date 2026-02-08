"""
Views for agents management
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Sum, Q

from apps.core.permissions import IsCashierOrOwner, IsOwner
from apps.inventory.models import Product, InventoryMovement
from .models import Agent, AgentLedger, AgentPayment
from .serializers import (
    AgentListSerializer, AgentDetailSerializer, AgentCreateUpdateSerializer,
    AgentLedgerSerializer, StockTransferSerializer,
    AgentPaymentSerializer, RecordPaymentSerializer
)


class AgentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for agent management
    """
    queryset = Agent.objects.select_related('created_by').all()
    permission_classes = [IsCashierOrOwner]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['full_name', 'phone_number', 'business_name', 'area']
    filterset_fields = ['is_active', 'is_trusted']
    ordering_fields = ['full_name', 'created_at', 'area']
    ordering = ['full_name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AgentListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AgentCreateUpdateSerializer
        return AgentDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def ledger(self, request, pk=None):
        """Get all ledger entries for an agent"""
        agent = self.get_object()
        ledger_entries = agent.ledger_entries.select_related('product', 'transferred_by').order_by('-transfer_date')
        
        serializer = AgentLedgerSerializer(ledger_entries, many=True)
        
        return Response({
            'success': True,
            'count': ledger_entries.count(),
            'results': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def debt_summary(self, request, pk=None):
        """Get debt summary for an agent"""
        agent = self.get_object()
        
        unpaid_entries = agent.ledger_entries.filter(is_paid=False)
        
        summary = {
            'total_debt': agent.total_debt,
            'debt_by_age': agent.get_debt_by_age(),
            'unpaid_entries_count': unpaid_entries.count(),
            'unpaid_entries': AgentLedgerSerializer(unpaid_entries, many=True).data
        }
        
        return Response({
            'success': True,
            'data': summary
        })
    
    @action(detail=True, methods=['post'])
    def transfer_stock(self, request, pk=None):
        """Transfer stock to agent"""
        agent = self.get_object()
        serializer = StockTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        product = data['product']
        quantity = data['quantity']
        unit_price = data['unit_price']
        debt_amount = data['debt_amount']
        notes = data.get('notes', '')
        
        with transaction.atomic():
            # Create inventory movement
            movement = InventoryMovement.objects.create(
                product=product,
                movement_type=InventoryMovement.TRANSFER_TO_AGENT,
                quantity_delta=-quantity,
                from_location='shop',
                to_location=f'agent_{agent.id}',
                reference_id=f'AGENT_TRANSFER_{agent.id}',
                performed_by=request.user,
                notes=f'Transfer to {agent.full_name}: {notes}'
            )
            
            # Create agent ledger entry
            ledger_entry = AgentLedger.objects.create(
                agent=agent,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                debt_amount=debt_amount,
                inventory_movement_id=str(movement.id),
                transferred_by=request.user,
                notes=notes
            )
            
            # Update product quantities
            product.quantity_in_stock -= quantity
            product.quantity_in_field += quantity
            product.save(update_fields=['quantity_in_stock', 'quantity_in_field', 'updated_at'])
        
        return Response({
            'success': True,
            'message': 'Stock transferred successfully',
            'data': {
                'ledger_entry': AgentLedgerSerializer(ledger_entry).data,
                'new_agent_debt': agent.total_debt + debt_amount
            }
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        """Record payment from agent"""
        agent = self.get_object()
        serializer = RecordPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        amount = data['amount']
        payment_method = data['payment_method']
        reference_number = data.get('reference_number', '')
        notes = data.get('notes', '')
        specific_entries = data.get('ledger_entries', [])
        
        with transaction.atomic():
            # Create payment record
            payment = AgentPayment.objects.create(
                agent=agent,
                amount=amount,
                payment_method=payment_method,
                reference_number=reference_number,
                received_by=request.user,
                notes=notes
            )
            
            # Apply payment to ledger entries
            remaining_amount = amount
            
            if specific_entries:
                # Apply to specific entries
                entries = AgentLedger.objects.filter(
                    id__in=specific_entries,
                    agent=agent,
                    is_paid=False
                ).order_by('transfer_date')
            else:
                # Apply to oldest unpaid entries first (FIFO)
                entries = AgentLedger.objects.filter(
                    agent=agent,
                    is_paid=False
                ).order_by('transfer_date')
            
            updated_entries = []
            for entry in entries:
                if remaining_amount <= 0:
                    break
                
                entry_remaining = entry.remaining_debt
                payment_to_apply = min(remaining_amount, entry_remaining)
                
                entry.paid_amount += payment_to_apply
                if entry.paid_amount >= entry.debt_amount:
                    entry.is_paid = True
                    entry.payment_date = payment.created_at
                
                entry.save(update_fields=['paid_amount', 'is_paid', 'payment_date', 'updated_at'])
                remaining_amount -= payment_to_apply
                updated_entries.append(entry)
        
        return Response({
            'success': True,
            'message': 'Payment recorded successfully',
            'data': {
                'payment': AgentPaymentSerializer(payment).data,
                'amount_applied': amount - remaining_amount,
                'amount_remaining': remaining_amount,
                'updated_entries_count': len(updated_entries),
                'new_total_debt': agent.total_debt
            }
        }, status=status.HTTP_201_CREATED)


class AgentLedgerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for agent ledger (read-only)
    """
    queryset = AgentLedger.objects.select_related(
        'agent', 'product', 'transferred_by'
    ).all()
    serializer_class = AgentLedgerSerializer
    permission_classes = [IsCashierOrOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['agent', 'product', 'is_paid']
    ordering_fields = ['transfer_date', 'created_at']
    ordering = ['-transfer_date']
    
    @action(detail=False, methods=['get'])
    def unpaid(self, request):
        """Get all unpaid ledger entries"""
        entries = self.get_queryset().filter(is_paid=False)
        
        # Optional: filter by agent
        agent_id = request.query_params.get('agent_id')
        if agent_id:
            entries = entries.filter(agent_id=agent_id)
        
        serializer = self.get_serializer(entries, many=True)
        total_debt = entries.aggregate(total=Sum('debt_amount'))['total'] or 0
        
        return Response({
            'success': True,
            'data': serializer.data,
            'total_debt': float(total_debt),
            'count': entries.count()
        })


class AgentPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for agent payments (read-only)
    """
    queryset = AgentPayment.objects.select_related('agent', 'received_by').all()
    serializer_class = AgentPaymentSerializer
    permission_classes = [IsCashierOrOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['agent', 'payment_method']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
