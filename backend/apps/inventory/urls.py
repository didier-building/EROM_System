"""
URL routing for inventory app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='category')
router.register('brands', views.BrandViewSet, basename='brand')
router.register('models', views.ModelViewSet, basename='model')
router.register('products', views.ProductViewSet, basename='product')
router.register('movements', views.InventoryMovementViewSet, basename='movement')

urlpatterns = [
    path('', include(router.urls)),
]
