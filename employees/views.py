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
        serializer.save()

class EmployeeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete employee (HR only)"""
    queryset = EmployeeProfile.objects.select_related('user', 'position', 'supervisor').prefetch_related('documents', 'notes')
    serializer_class = EmployeeProfileDetailSerializer
    permission_classes = [IsHRPermission]
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete - deactivate employee instead of hard delete"""
        employee = self.get_object()
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
