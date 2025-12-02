from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Sum
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import date, timedelta

from .models import (
    LeaveType, LeaveBalance, LeaveApplication, 
    LeaveApplicationAttachment, LeaveApplicationComment
)
from .serializers import (
    LeaveTypeSerializer, LeaveBalanceSerializer, LeaveApplicationDetailSerializer,
    LeaveApplicationListSerializer, LeaveApplicationCreateSerializer,
    LeaveApplicationApprovalSerializer, LeaveApplicationAttachmentSerializer,
    LeaveApplicationCommentSerializer
)
from accounts.views import IsHRPermission

User = get_user_model()

# Leave Type Management

class LeaveTypeListCreateAPIView(generics.ListCreateAPIView):
    """List all leave types or create new type (HR only for creation)"""
    queryset = LeaveType.objects.filter(is_active=True).order_by('name')
    serializer_class = LeaveTypeSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsHRPermission()]
        return [permissions.IsAuthenticated()]

class LeaveTypeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete leave type (HR only)"""
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsHRPermission]

# Leave Applications

class LeaveApplicationListCreateAPIView(generics.ListCreateAPIView):
    """List leave applications or create new application"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_hr:
            # HR can see all applications
            queryset = LeaveApplication.objects.select_related(
                'employee', 'leave_type', 'approved_by'
            ).all()
        else:
            # Employees can only see their own applications
            queryset = LeaveApplication.objects.select_related(
                'leave_type', 'approved_by'
            ).filter(employee=user)
        
        # Filter parameters
        status_filter = self.request.query_params.get('status')
        leave_type = self.request.query_params.get('leave_type')
        year = self.request.query_params.get('year')
        employee = self.request.query_params.get('employee')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if leave_type:
            queryset = queryset.filter(leave_type__name__icontains=leave_type)
        
        if year:
            queryset = queryset.filter(start_date__year=year)
        
        if employee and user.is_hr:
            queryset = queryset.filter(
                Q(employee__username__icontains=employee) |
                Q(employee__first_name__icontains=employee) |
                Q(employee__last_name__icontains=employee)
            )
        
        return queryset.order_by('-applied_on')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LeaveApplicationCreateSerializer
        return LeaveApplicationListSerializer

class LeaveApplicationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete leave application"""
    serializer_class = LeaveApplicationDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_hr:
            return LeaveApplication.objects.select_related(
                'employee', 'leave_type', 'approved_by', 'replacement_employee'
            ).prefetch_related('attachments', 'comments').all()
        else:
            return LeaveApplication.objects.select_related(
                'leave_type', 'approved_by', 'replacement_employee'
            ).prefetch_related('attachments', 'comments').filter(employee=user)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Employees can only update their own pending applications
        if not request.user.is_hr and instance.employee != request.user:
            return Response(
                {'error': 'You can only update your own leave applications.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if instance.status != 'PENDING':
            return Response(
                {'error': 'Cannot update non-pending leave applications.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Only allow deletion of own pending applications
        if instance.employee != request.user:
            return Response(
                {'error': 'You can only cancel your own leave applications.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if instance.status != 'PENDING':
            return Response(
                {'error': 'Cannot cancel non-pending leave applications.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.status = 'CANCELLED'
        instance.save()
        
        return Response(
            {'message': 'Leave application cancelled successfully.'}, 
            status=status.HTTP_200_OK
        )

class LeaveApplicationApprovalAPIView(APIView):
    """HR approval/rejection of leave applications"""
    permission_classes = [IsHRPermission]
    
    def post(self, request, pk):
        try:
            leave_application = LeaveApplication.objects.get(pk=pk)
        except LeaveApplication.DoesNotExist:
            return Response(
                {'error': 'Leave application not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if leave_application.status != 'PENDING':
            return Response(
                {'error': 'Leave application is not pending.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = LeaveApplicationApprovalSerializer(
            leave_application, 
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                LeaveApplicationDetailSerializer(leave_application, context={'request': request}).data
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Leave Balance Management

class LeaveBalanceListAPIView(generics.ListAPIView):
    """List leave balances"""
    serializer_class = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        year = self.request.query_params.get('year', date.today().year)
        
        if user.is_hr:
            employee_id = self.request.query_params.get('employee')
            if employee_id:
                return LeaveBalance.objects.select_related(
                    'user', 'leave_type'
                ).filter(user_id=employee_id, year=year)
            else:
                return LeaveBalance.objects.select_related(
                    'user', 'leave_type'
                ).filter(year=year)
        else:
            return LeaveBalance.objects.select_related(
                'leave_type'
            ).filter(user=user, year=year)

class MyLeaveBalanceAPIView(generics.ListAPIView):
    """Get current user's leave balances"""
    serializer_class = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        year = self.request.query_params.get('year', date.today().year)
        return LeaveBalance.objects.select_related(
            'leave_type'
        ).filter(user=self.request.user, year=year)

# Leave Application Attachments

class LeaveApplicationAttachmentListCreateAPIView(generics.ListCreateAPIView):
    """List or upload attachments for leave application"""
    serializer_class = LeaveApplicationAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        leave_app_id = self.kwargs['leave_app_id']
        leave_app = get_object_or_404(LeaveApplication, id=leave_app_id)
        
        # Check permissions
        if not self.request.user.is_hr and leave_app.employee != self.request.user:
            return LeaveApplicationAttachment.objects.none()
        
        return leave_app.attachments.all()
    
    def perform_create(self, serializer):
        leave_app_id = self.kwargs['leave_app_id']
        leave_app = get_object_or_404(LeaveApplication, id=leave_app_id)
        
        # Check permissions
        if not self.request.user.is_hr and leave_app.employee != self.request.user:
            raise permissions.PermissionDenied("You can only manage attachments for your own leave applications.")
        
        serializer.save(
            leave_application=leave_app, 
            uploaded_by=self.request.user
        )

# Leave Application Comments

class LeaveApplicationCommentListCreateAPIView(generics.ListCreateAPIView):
    """List or add comments to leave application"""
    serializer_class = LeaveApplicationCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        leave_app_id = self.kwargs['leave_app_id']
        leave_app = get_object_or_404(LeaveApplication, id=leave_app_id)
        
        # Check permissions
        if not self.request.user.is_hr and leave_app.employee != self.request.user:
            return LeaveApplicationComment.objects.none()
        
        comments = leave_app.comments.all()
        
        # Non-HR users cannot see internal comments
        if not self.request.user.is_hr:
            comments = comments.filter(is_internal=False)
        
        return comments
    
    def perform_create(self, serializer):
        leave_app_id = self.kwargs['leave_app_id']
        leave_app = get_object_or_404(LeaveApplication, id=leave_app_id)
        
        # Check permissions
        if not self.request.user.is_hr and leave_app.employee != self.request.user:
            raise permissions.PermissionDenied("You can only comment on your own leave applications.")
        
        serializer.save(
            leave_application=leave_app, 
            author=self.request.user
        )

# Statistics and Reports

@api_view(['GET'])
@permission_classes([IsHRPermission])
def leave_statistics(request):
    """Get comprehensive leave statistics"""
    current_year = date.today().year
    
    # Overall statistics
    total_applications = LeaveApplication.objects.count()
    pending_applications = LeaveApplication.objects.filter(status='PENDING').count()
    approved_applications = LeaveApplication.objects.filter(status='APPROVED').count()
    rejected_applications = LeaveApplication.objects.filter(status='REJECTED').count()
    
    # Monthly breakdown for current year
    monthly_stats = []
    for month in range(1, 13):
        month_applications = LeaveApplication.objects.filter(
            start_date__year=current_year,
            start_date__month=month
        ).count()
        monthly_stats.append({
            'month': month,
            'applications': month_applications
        })
    
    # Leave type breakdown
    leave_type_stats = LeaveApplication.objects.values(
        'leave_type__name'
    ).annotate(
        count=Count('id'),
        total_days=Sum('total_days')
    ).order_by('-count')
    
    # Department breakdown
    department_stats = LeaveApplication.objects.values(
        'employee__department'
    ).annotate(
        count=Count('id'),
        total_days=Sum('total_days')
    ).order_by('-count')
    
    # Most active employees
    top_applicants = LeaveApplication.objects.values(
        'employee__username',
        'employee__first_name',
        'employee__last_name'
    ).annotate(
        total_applications=Count('id'),
        total_days=Sum('total_days')
    ).order_by('-total_applications')[:10]
    
    stats = {
        'summary': {
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'approved_applications': approved_applications,
            'rejected_applications': rejected_applications,
        },
        'monthly_breakdown': monthly_stats,
        'leave_type_breakdown': list(leave_type_stats),
        'department_breakdown': list(department_stats),
        'top_applicants': list(top_applicants),
    }
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_leave_summary(request):
    """Get current user's leave summary"""
    user = request.user
    current_year = date.today().year
    
    # Applications summary
    total_applications = user.leave_applications.count()
    pending_applications = user.leave_applications.filter(status='PENDING').count()
    approved_applications = user.leave_applications.filter(status='APPROVED').count()
    
    # Leave balances
    balances = LeaveBalance.objects.filter(user=user, year=current_year)
    balance_data = LeaveBalanceSerializer(balances, many=True).data
    
    # Recent applications
    recent_applications = user.leave_applications.select_related(
        'leave_type'
    )[:5]
    recent_data = LeaveApplicationListSerializer(recent_applications, many=True).data
    
    # Upcoming leaves
    upcoming_leaves = user.leave_applications.filter(
        status='APPROVED',
        start_date__gte=date.today()
    ).select_related('leave_type')[:3]
    upcoming_data = LeaveApplicationListSerializer(upcoming_leaves, many=True).data
    
    summary = {
        'applications_summary': {
            'total': total_applications,
            'pending': pending_applications,
            'approved': approved_applications,
        },
        'leave_balances': balance_data,
        'recent_applications': recent_data,
        'upcoming_leaves': upcoming_data,
    }
    
    return Response(summary)

@api_view(['POST'])
@permission_classes([IsHRPermission])
def bulk_approve_leaves(request):
    """Bulk approve multiple leave applications"""
    application_ids = request.data.get('application_ids', [])
    approval_comments = request.data.get('approval_comments', '')
    
    if not application_ids:
        return Response(
            {'error': 'No application IDs provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    applications = LeaveApplication.objects.filter(
        id__in=application_ids, 
        status='PENDING'
    )
    
    updated_count = 0
    for app in applications:
        app.status = 'APPROVED'
        app.approval_comments = approval_comments
        app.approved_by = request.user
        app.approved_on = timezone.now()
        app.save()
        updated_count += 1
    
    return Response({
        'message': f'Successfully approved {updated_count} leave applications',
        'updated_count': updated_count
    })
