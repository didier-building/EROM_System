"""
Custom exception handler for REST API
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        # Standardize error format
        custom_response = {
            'success': False,
            'error': {
                'message': str(exc),
                'code': response.status_code,
                'details': response.data if isinstance(response.data, dict) else {'detail': response.data}
            }
        }
        return Response(custom_response, status=response.status_code)
    
    return response
