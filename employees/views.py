from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import EmployeeProfile, Position, EmployeeDocument, EmployeeNote
from .serializers import (
    EmployeeProfileDetailSerializer, EmployeeProfileListSerializer,
    EmployeeCreateSerializer, PositionSerializer, EmployeeDocumentSerializer,
    EmployeeNoteSerializer
)
from accounts.views import IsHRPermission

User = get_user_model()

# Employee CRUD Operations

class EmployeeListCreateAPIView(generics.ListCreateAPIView):
    """List all employees or create a new employee (HR only)"""
    permission_classes = [IsHRPermission]
    
    def get_queryset(self):
        queryset = EmployeeProfile.objects.select_related('user', 'position', 'supervisor').all()
        
        # Filter parameters
        search = self.request.query_params.get('search')
        department = self.request.query_params.get('department')
        position = self.request.query_params.get('position')
        status = self.request.query_params.get('status')
        employment_type = self.request.query_params.get('employment_type')
        
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__employee_id__icontains=search)
            )
        
        if department:
            queryset = queryset.filter(user__department__icontains=department)
            
        if position:
            queryset = queryset.filter(position__title__icontains=position)
            
        if status:
            queryset = queryset.filter(status=status)
            
        if employment_type:
            queryset = queryset.filter(employment_type=employment_type)
            
        return queryset.order_by('user__last_name', 'user__first_name')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EmployeeCreateSerializer
        return EmployeeProfileListSerializer
    
    def perform_create(self, serializer):
        print(f"Creating employee with data: {self.request.data}")
        serializer.save()
        
    def create(self, request, *args, **kwargs):
        print(f"Received POST request to create employee")
        print(f"Request data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        print(f"Validating data...")
        if not serializer.is_valid():
            print(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"Data is valid, creating employee...")
        self.perform_create(serializer)
        
        # Get the created instance and add email info to response
        response_data = serializer.data
        instance = serializer.instance
        
        # Include email status in response
        if hasattr(instance, '_email_sent'):
            response_data['email_sent'] = instance._email_sent
            response_data['temporary_password'] = instance._temporary_password
            if instance._email_sent:
                response_data['message'] = f"Employee created successfully. Login credentials have been sent to {instance.user.email}"
            else:
                response_data['message'] = "Employee created successfully, but email could not be sent. Please provide credentials manually."
        
        headers = self.get_success_headers(response_data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

class EmployeeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete employee (HR only)"""
    queryset = EmployeeProfile.objects.select_related('user', 'position', 'supervisor').prefetch_related('documents', 'notes')
    serializer_class = EmployeeProfileDetailSerializer
    permission_classes = [IsHRPermission]
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete - deactivate employee instead of hard delete"""
        employee = self.get_object()
        
        # Prevent HR from deleting themselves
        if employee.user == request.user:
            return Response({
                'error': 'You cannot delete your own account. Please contact another HR manager.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Soft delete: deactivate instead of hard delete
        employee.status = 'TERMINATED'
        employee.user.is_active = False
        employee.save()
        employee.user.save()
        
        return Response({
            'message': f'Employee {employee.full_name} has been deactivated successfully.'
        }, status=status.HTTP_200_OK)

class EmployeeProfileAPIView(generics.RetrieveUpdateAPIView):
    """Employee can view and update their own profile"""
    serializer_class = EmployeeProfileDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        employee_profile, created = EmployeeProfile.objects.get_or_create(
            user=self.request.user,
            defaults={'status': 'ACTIVE', 'employment_type': 'FULL_TIME'}
        )
        return employee_profile

# Position Management

class PositionListCreateAPIView(generics.ListCreateAPIView):
    """List all positions or create new position (HR only)"""
    queryset = Position.objects.all().order_by('level', 'title')
    serializer_class = PositionSerializer
    permission_classes = [IsHRPermission]

class PositionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete position (HR only)"""
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [IsHRPermission]

# Employee Documents

class EmployeeDocumentListCreateAPIView(generics.ListCreateAPIView):
    """List or create employee documents"""
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        employee_id = self.kwargs['employee_id']
        employee = get_object_or_404(EmployeeProfile, id=employee_id)
        
        # HR can see all documents, employees can only see their own
        if self.request.user.is_hr or employee.user == self.request.user:
            return employee.documents.all()
        else:
            return EmployeeDocument.objects.none()
    
    def perform_create(self, serializer):
        employee_id = self.kwargs['employee_id']
        employee = get_object_or_404(EmployeeProfile, id=employee_id)
        
        # HR can add documents for any employee, employees can add to their own profile
        if self.request.user.is_hr or employee.user == self.request.user:
            serializer.save(employee=employee, uploaded_by=self.request.user)
        else:
            raise permissions.PermissionDenied("You can only manage your own documents.")

class EmployeeDocumentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete employee document"""
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        employee_id = self.kwargs['employee_id']
        employee = get_object_or_404(EmployeeProfile, id=employee_id)
        
        if self.request.user.is_hr or employee.user == self.request.user:
            return employee.documents.all()
        else:
            return EmployeeDocument.objects.none()

# Employee Notes

class EmployeeNoteListCreateAPIView(generics.ListCreateAPIView):
    """List or create employee notes (HR only)"""
    serializer_class = EmployeeNoteSerializer
    permission_classes = [IsHRPermission]
    
    def get_queryset(self):
        employee_id = self.kwargs['employee_id']
        employee = get_object_or_404(EmployeeProfile, id=employee_id)
        return employee.notes.all()
    
    def perform_create(self, serializer):
        employee_id = self.kwargs['employee_id']
        employee = get_object_or_404(EmployeeProfile, id=employee_id)
        serializer.save(employee=employee, author=self.request.user)

class EmployeeNoteDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete employee note (HR only)"""
    serializer_class = EmployeeNoteSerializer
    permission_classes = [IsHRPermission]
    
    def get_queryset(self):
        employee_id = self.kwargs['employee_id']
        employee = get_object_or_404(EmployeeProfile, id=employee_id)
        return employee.notes.all()

# Statistics and Reports

@api_view(['GET'])
@permission_classes([IsHRPermission])
def employee_statistics(request):
    """Get comprehensive employee statistics"""
    total_employees = EmployeeProfile.objects.count()
    active_employees = EmployeeProfile.objects.filter(status='ACTIVE').count()
    
    # Status breakdown
    status_breakdown = EmployeeProfile.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Employment type breakdown
    employment_breakdown = EmployeeProfile.objects.values('employment_type').annotate(
        count=Count('id')
    ).order_by('employment_type')
    
    # Department breakdown
    department_breakdown = EmployeeProfile.objects.values(
        'user__department'
    ).annotate(
        count=Count('id')
    ).order_by('user__department')
    
    # Position breakdown
    position_breakdown = EmployeeProfile.objects.values(
        'position__title'
    ).annotate(
        count=Count('id')
    ).order_by('position__title')
    
    stats = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': total_employees - active_employees,
        'status_breakdown': list(status_breakdown),
        'employment_breakdown': list(employment_breakdown),
        'department_breakdown': list(department_breakdown),
        'position_breakdown': list(position_breakdown),
    }
    
    return Response(stats)

@api_view(['POST'])
@permission_classes([IsHRPermission])
def bulk_update_employees(request):
    """Bulk update multiple employees"""
    employee_ids = request.data.get('employee_ids', [])
    update_data = request.data.get('update_data', {})
    
    if not employee_ids:
        return Response({'error': 'No employee IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    employees = EmployeeProfile.objects.filter(id__in=employee_ids)
    updated_count = employees.count()
    
    # Update allowed fields
    allowed_fields = ['status', 'employment_type', 'supervisor']
    
    for field, value in update_data.items():
        if field in allowed_fields:
            if field == 'supervisor':
                try:
                    supervisor = User.objects.get(id=value, role='HR')
                    employees.update(supervisor=supervisor)
                except User.DoesNotExist:
                    return Response(
                        {'error': f'Invalid supervisor ID: {value}'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                employees.update(**{field: value})
    
    return Response({
        'message': f'Successfully updated {updated_count} employees',
        'updated_count': updated_count
    })


@api_view(['POST'])
@permission_classes([IsHRPermission])
def resend_employee_credentials(request, employee_id):
    """Resend login credentials email to an employee"""
    from .email_utils import send_temporary_password_email
    import secrets
    import string
    
    try:
        employee_profile = EmployeeProfile.objects.select_related('user').get(id=employee_id)
        user = employee_profile.user
        
        # Check if user must change password (meaning they haven't logged in yet)
        if not user.must_change_password:
            return Response({
                'error': 'Employee has already changed their password. Cannot resend temporary credentials.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate new temporary password
        alphabet = string.ascii_letters + string.digits + '@#$%'
        new_password = ''.join(secrets.choice(alphabet) for i in range(12))
        
        # Update user password
        user.set_password(new_password)
        user.must_change_password = True
        user.save()
        
        # Send email
        employee_full_name = f"{user.first_name} {user.last_name}"
        email_sent = send_temporary_password_email(
            employee_email=user.email,
            employee_name=employee_full_name,
            username=user.username,
            temporary_password=new_password
        )
        
        if email_sent:
            return Response({
                'success': True,
                'message': f'Login credentials have been sent to {user.email}',
                'email': user.email,
                'temporary_password': new_password
            })
        else:
            return Response({
                'success': False,
                'message': 'Failed to send email. Please share credentials manually.',
                'email': user.email,
                'temporary_password': new_password
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except EmployeeProfile.DoesNotExist:
        return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
