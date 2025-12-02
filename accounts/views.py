from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q, Count
from datetime import datetime, timedelta
from .models import CustomUser, Department
from .serializers import (
    UserSerializer, LoginSerializer, EmployeeListSerializer, 
    DepartmentSerializer, ChangePasswordSerializer, DashboardStatsSerializer
)


class LoginAPIView(APIView):
    """API view for user login with JWT tokens"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """API view for user logout"""
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    """API view for user profile management"""
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user


class ChangePasswordAPIView(APIView):
    """API view for changing user password"""
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardAPIView(APIView):
    """API view for dashboard statistics"""
    
    def get(self, request):
        user = request.user
        
        if user.is_hr:
            # HR can see all statistics
            stats = {
                'total_employees': CustomUser.objects.filter(role='EMPLOYEE').count(),
                'total_hr': CustomUser.objects.filter(role='HR').count(),
                'total_departments': Department.objects.count(),
                'active_employees': CustomUser.objects.filter(role='EMPLOYEE', is_active=True).count(),
                'recent_logins': CustomUser.objects.filter(
                    last_login__gte=datetime.now() - timedelta(days=7)
                ).count(),
            }
            serializer = DashboardStatsSerializer(stats)
            return Response({
                'user': UserSerializer(user).data,
                'stats': serializer.data,
                'role': 'HR'
            })
        else:
            # Employee sees limited information
            return Response({
                'user': UserSerializer(user).data,
                'role': 'EMPLOYEE'
            })


# HR-only permission class
class IsHRPermission(permissions.BasePermission):
    """Custom permission to only allow HR users"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_hr


class EmployeeListAPIView(generics.ListCreateAPIView):
    """API view for listing and creating employees (HR only)"""
    serializer_class = EmployeeListSerializer
    permission_classes = [IsHRPermission]
    
    def get_queryset(self):
        queryset = CustomUser.objects.filter(role='EMPLOYEE')
        search = self.request.query_params.get('search')
        department = self.request.query_params.get('department')
        active = self.request.query_params.get('active')
        
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(email__icontains=search)
            )
        
        if department:
            queryset = queryset.filter(department__icontains=department)
            
        if active is not None:
            queryset = queryset.filter(is_active=active.lower() == 'true')
            
        return queryset.order_by('username')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserSerializer
        return EmployeeListSerializer


class EmployeeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """API view for employee detail management (HR only)"""
    serializer_class = UserSerializer
    permission_classes = [IsHRPermission]
    
    def get_queryset(self):
        return CustomUser.objects.filter(role='EMPLOYEE')


class DepartmentListAPIView(generics.ListCreateAPIView):
    """API view for department management (HR only)"""
    queryset = Department.objects.all().order_by('name')
    serializer_class = DepartmentSerializer
    permission_classes = [IsHRPermission]


class DepartmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """API view for department detail management (HR only)"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsHRPermission]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_info(request):
    """API endpoint to get current user information"""
    return Response(UserSerializer(request.user).data)


@api_view(['GET'])
@permission_classes([IsHRPermission])
def employee_stats(request):
    """API endpoint for employee statistics (HR only)"""
    stats = {
        'total_employees': CustomUser.objects.filter(role='EMPLOYEE').count(),
        'active_employees': CustomUser.objects.filter(role='EMPLOYEE', is_active=True).count(),
        'inactive_employees': CustomUser.objects.filter(role='EMPLOYEE', is_active=False).count(),
        'employees_by_department': list(
            CustomUser.objects.filter(role='EMPLOYEE')
            .values('department')
            .annotate(count=Count('id'))
            .order_by('department')
        )
    }
    return Response(stats)
