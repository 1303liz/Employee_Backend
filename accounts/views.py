from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate
from django.db.models import Q, Count
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from drf_spectacular.openapi import OpenApiTypes
from .models import CustomUser, Department, UserDocument
from .serializers import (
    UserSerializer, LoginSerializer, RegisterSerializer, LogoutSerializer, EmployeeListSerializer, 
    DepartmentSerializer, ChangePasswordSerializer, DashboardStatsSerializer, UserDocumentSerializer
)


class LoginAPIView(APIView):
    """API view for user login with JWT tokens"""
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer
    
    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Login successful",
                examples=[
                    OpenApiExample(
                        "Login Success",
                        value={
                            "user": {
                                "id": 1,
                                "username": "john_doe",
                                "email": "john@example.com",
                                "first_name": "John",
                                "last_name": "Doe",
                                "role": "EMPLOYEE",
                                "employee_id": "EMP001",
                                "department": "Engineering",
                                "phone_number": "+1234567890",
                                "hire_date": "2023-01-15",
                                "is_active": True
                            },
                            "tokens": {
                                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                                "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid credentials or validation error",
                examples=[
                    OpenApiExample(
                        "Invalid Credentials",
                        value={"non_field_errors": ["Invalid credentials."]}
                    ),
                    OpenApiExample(
                        "Missing Fields",
                        value={"non_field_errors": ["Must provide username and password."]}
                    )
                ]
            )
        },
        summary="User Login",
        description="Authenticate user with username and password, returns JWT tokens",
        tags=["Authentication"]
    )
    def post(self, request):
        print(f"Login attempt - Request data: {request.data}")
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
        print(f"Login validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterAPIView(APIView):
    """API view for user registration"""
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    
    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Registration successful",
                examples=[
                    OpenApiExample(
                        "Registration Success",
                        value={
                            "user": {
                                "id": 1,
                                "username": "john_doe",
                                "email": "john@example.com",
                                "first_name": "John",
                                "last_name": "Doe",
                                "role": "EMPLOYEE",
                                "employee_id": "EMP001",
                                "department": "Engineering",
                                "phone_number": "+1234567890",
                                "hire_date": "2023-01-15",
                                "is_active": True
                            },
                            "tokens": {
                                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                                "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "Username Exists",
                        value={"username": ["A user with that username already exists."]}
                    ),
                    OpenApiExample(
                        "Email Exists",
                        value={"email": ["User with this email address already exists."]}
                    )
                ]
            )
        },
        summary="User Registration",
        description="Register a new user account and return JWT tokens",
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """API view for user logout"""
    serializer_class = LogoutSerializer
    
    @extend_schema(
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(
                description="Successfully logged out",
                examples=[
                    OpenApiExample(
                        "Logout Success",
                        value={"message": "Successfully logged out"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid token",
                examples=[
                    OpenApiExample(
                        "Invalid Token",
                        value={"error": "Invalid token"}
                    )
                ]
            )
        },
        summary="User Logout",
        description="Blacklist the refresh token to logout user",
        tags=["Authentication"]
    )
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
    serializer_class = ChangePasswordSerializer
    
    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="Password changed successfully",
                examples=[
                    OpenApiExample(
                        "Password Change Success",
                        value={"message": "Password changed successfully"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "Old Password Incorrect",
                        value={"old_password": ["Old password is incorrect."]}
                    ),
                    OpenApiExample(
                        "Passwords Don't Match",
                        value={"non_field_errors": ["New passwords don't match."]}
                    )
                ]
            )
        },
        summary="Change Password",
        description="Change the current user's password",
        tags=["Authentication"]
    )
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


class ProfileDetailAPIView(generics.RetrieveAPIView):
    """API view to retrieve current user's profile"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ProfileUpdateAPIView(generics.UpdateAPIView):
    """API view to update current user's profile"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class UserDocumentListCreateAPIView(generics.ListCreateAPIView):
    """API view to list and create user documents"""
    serializer_class = UserDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return UserDocument.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserDocumentDetailAPIView(generics.RetrieveDestroyAPIView):
    """API view to retrieve or delete a specific user document"""
    serializer_class = UserDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserDocument.objects.filter(user=self.request.user)

