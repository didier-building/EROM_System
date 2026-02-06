"""
URL Configuration for EROM System
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    # API endpoints
    path('api/auth/', include('apps.core.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/agents/', include('apps.agents.urls')),
    path('api/sales/', include('apps.sales.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/licensing/', include('apps.licensing.urls')),
    path('api/audit/', include('apps.audit.urls')),
    
    # Health check endpoint for Electron
    path('health/', lambda request: __import__('django.http').JsonResponse({'status': 'ok'})),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
