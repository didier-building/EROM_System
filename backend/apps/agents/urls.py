"""
URL routing for agents app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('agents', views.AgentViewSet, basename='agent')
router.register('ledger', views.AgentLedgerViewSet, basename='ledger')
router.register('payments', views.AgentPaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]
