"""
URL configuration for employee_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint with available endpoints"""
    return Response({
        'message': 'Employee Management System API',
        'version': '1.0',
        'status': 'active',
        'endpoints': {
            'authentication': {
                'login': '/api/login/',
                'logout': '/api/logout/',
                'refresh': '/api/refresh/',
                'profile': '/api/profile/',
                'dashboard': '/api/dashboard/',
            },
            'employee_management': {
                'employees': '/api/employee-management/',
                'positions': '/api/employee-management/positions/',
                'statistics': '/api/employee-management/statistics/',
            },
            'leave_management': {
                'applications': '/api/leave-management/applications/',
                'types': '/api/leave-management/types/',
                'my_balances': '/api/leave-management/my-balances/',
            },
            'attendance_management': {
                'check_in': '/api/attendance-management/check-in/',
                'check_out': '/api/attendance-management/check-out/',
                'records': '/api/attendance-management/records/',
                'statistics': '/api/attendance-management/statistics/',
            },
            'messaging': {
                'messages': '/api/messaging/messages/',
                'inbox': '/api/messaging/messages/inbox/',
                'sent': '/api/messaging/messages/sent/',
                'announcements': '/api/messaging/announcements/',
            },
            'admin': '/admin/'
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_root, name='root'),
    path('api/', api_root, name='api_root'),  # API root at /api/
    path('api/docs/', api_root, name='api_docs'),
    # API Schema and Documentation URLs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # API Endpoints
    path('api/', include('accounts.urls')),
    path('api/employee-management/', include('employees.urls')),
    path('api/leave-management/', include('leave.urls')),
    path('api/attendance-management/', include('attendance.urls')),
    path('api/messaging/', include('messaging.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
