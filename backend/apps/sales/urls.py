"""
URL routing for sales app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('transactions', views.TransactionViewSet, basename='transaction')
router.register('reconciliations', views.ReconciliationViewSet, basename='reconciliation')

urlpatterns = [
    path('', include(router.urls)),
]
