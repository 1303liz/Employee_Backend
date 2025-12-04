from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Sum, Avg
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import date, timedelta, datetime

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

# Reports and Analytics

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def employee_leave_report(request):
    """Generate detailed leave report for an employee"""
    employee_id = request.query_params.get('employee_id')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    year = request.query_params.get('year')
    
    # If no employee_id provided, use current user
    if not employee_id:
        employee = request.user
    else:
        # Only HR can view other employees' reports
        if request.user.role != 'HR':
            return Response(
                {'error': 'You can only view your own leave report'},
                status=status.HTTP_403_FORBIDDEN
            )
        employee = get_object_or_404(User, id=employee_id)
    
    # Determine date range
    if year:
        year = int(year)
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
    else:
        if not end_date:
            end_date = date.today()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not start_date:
            start_date = date(end_date.year, 1, 1)  # Beginning of current year
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    # Get leave applications
    applications = LeaveApplication.objects.filter(
        employee=employee,
        start_date__gte=start_date,
        end_date__lte=end_date
    ).select_related('leave_type', 'approved_by')
    
    # Statistics by status
    status_stats = {
        'pending': applications.filter(status='PENDING').count(),
        'approved': applications.filter(status='APPROVED').count(),
        'rejected': applications.filter(status='REJECTED').count(),
        'cancelled': applications.filter(status='CANCELLED').count(),
        'total': applications.count(),
    }
    
    # Statistics by leave type
    leave_type_stats = []
    leave_types = LeaveType.objects.filter(is_active=True)
    
    for lt in leave_types:
        type_apps = applications.filter(leave_type=lt)
        approved_apps = type_apps.filter(status='APPROVED')
        
        # Calculate total days used
        total_days_used = sum([app.total_days for app in approved_apps])
        
        # Get balance
        try:
            balance = LeaveBalance.objects.get(employee=employee, leave_type=lt)
            remaining = balance.remaining_days
            total_allocated = balance.total_days
        except LeaveBalance.DoesNotExist:
            remaining = lt.max_days_per_year or 0
            total_allocated = lt.max_days_per_year or 0
        
        leave_type_stats.append({
            'leave_type': lt.name,
            'total_allocated': total_allocated,
            'days_used': total_days_used,
            'days_remaining': remaining,
            'applications_count': type_apps.count(),
            'pending_count': type_apps.filter(status='PENDING').count(),
            'utilization_rate': round((total_days_used / total_allocated * 100), 2) if total_allocated > 0 else 0,
        })
    
    # Monthly distribution
    from datetime import datetime
    monthly_stats = {}
    for month in range(1, 13):
        month_apps = applications.filter(
            start_date__month=month,
            status='APPROVED'
        )
        monthly_stats[datetime(2000, month, 1).strftime('%B')] = {
            'count': month_apps.count(),
            'days': sum([app.total_days for app in month_apps])
        }
    
    # Recent applications
    recent_apps = applications.order_by('-created_at')[:10]
    
    report = {
        'employee': {
            'id': employee.id,
            'username': employee.username,
            'email': employee.email,
            'full_name': f"{employee.first_name} {employee.last_name}",
            'role': employee.role,
        },
        'period': {
            'start_date': start_date,
            'end_date': end_date,
        },
        'summary': {
            'total_applications': status_stats['total'],
            'approved_applications': status_stats['approved'],
            'pending_applications': status_stats['pending'],
            'rejected_applications': status_stats['rejected'],
            'total_days_taken': sum([app.total_days for app in applications.filter(status='APPROVED')]),
            'average_leave_duration': round(sum([app.total_days for app in applications.filter(status='APPROVED')]) / status_stats['approved'], 2) if status_stats['approved'] > 0 else 0,
        },
        'status_breakdown': status_stats,
        'leave_type_breakdown': leave_type_stats,
        'monthly_distribution': monthly_stats,
        'recent_applications': LeaveApplicationListSerializer(recent_apps, many=True, context={'request': request}).data,
        'performance_metrics': {
            'leave_utilization': round(sum([lt['utilization_rate'] for lt in leave_type_stats]) / len(leave_type_stats), 2) if leave_type_stats else 0,
            'planning_score': round((status_stats['approved'] / status_stats['total'] * 100), 2) if status_stats['total'] > 0 else 0,
        }
    }
    
    return Response(report)

@api_view(['GET'])
@permission_classes([IsHRPermission])
def team_leave_report(request):
    """Generate leave report for all employees (HR only)"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    department = request.query_params.get('department')
    year = request.query_params.get('year')
    
    # Determine date range
    if year:
        year = int(year)
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
    else:
        if not end_date:
            end_date = date.today()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not start_date:
            start_date = date(end_date.year, 1, 1)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    # Get employees
    employees = User.objects.filter(role='EMPLOYEE', is_active=True)
    if department:
        employees = employees.filter(employee_profile__department__name=department)
    
    # Generate report for each employee
    team_data = []
    for emp in employees:
        applications = LeaveApplication.objects.filter(
            employee=emp,
            start_date__gte=start_date,
            end_date__lte=end_date
        )
        
        approved_apps = applications.filter(status='APPROVED')
        pending_apps = applications.filter(status='PENDING')
        total_days_taken = sum([app.total_days for app in approved_apps])
        
        # Get total allocated days
        balances = LeaveBalance.objects.filter(employee=emp)
        total_allocated = sum([b.total_days for b in balances])
        total_remaining = sum([b.remaining_days for b in balances])
        
        team_data.append({
            'employee_id': emp.id,
            'employee_name': f"{emp.first_name} {emp.last_name}",
            'email': emp.email,
            'department': emp.employee_profile.department.name if hasattr(emp, 'employee_profile') and emp.employee_profile.department else 'N/A',
            'total_applications': applications.count(),
            'approved_applications': approved_apps.count(),
            'pending_applications': pending_apps.count(),
            'days_taken': total_days_taken,
            'days_allocated': total_allocated,
            'days_remaining': total_remaining,
            'utilization_rate': round((total_days_taken / total_allocated * 100), 2) if total_allocated > 0 else 0,
        })
    
    # Sort by utilization rate
    team_data.sort(key=lambda x: x['utilization_rate'], reverse=True)
    
    # Calculate team averages
    team_summary = {
        'total_employees': len(team_data),
        'total_leave_applications': sum(e['total_applications'] for e in team_data),
        'total_days_taken': sum(e['days_taken'] for e in team_data),
        'average_utilization': round(sum(e['utilization_rate'] for e in team_data) / len(team_data), 2) if team_data else 0,
        'pending_applications': sum(e['pending_applications'] for e in team_data),
    }
    
    # Leave type distribution across team
    leave_type_dist = LeaveApplication.objects.filter(
        employee__in=employees,
        start_date__gte=start_date,
        end_date__lte=end_date,
        status='APPROVED'
    ).values('leave_type__name').annotate(
        count=Count('id'),
        total_days=Sum('total_days')
    ).order_by('-count')
    
    report = {
        'period': {
            'start_date': start_date,
            'end_date': end_date,
        },
        'team_summary': team_summary,
        'leave_type_distribution': list(leave_type_dist),
        'employee_details': team_data,
    }
    
    return Response(report)

@api_view(['GET'])
@permission_classes([IsHRPermission])
def leave_analytics(request):
    """Generate leave analytics and insights (HR only)"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    # Default to current year
    if not end_date:
        end_date = date.today()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = date(end_date.year, 1, 1)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    applications = LeaveApplication.objects.filter(
        start_date__gte=start_date,
        end_date__lte=end_date
    )
    
    # Status distribution
    status_distribution = applications.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Leave type popularity
    leave_type_stats = applications.values('leave_type__name').annotate(
        count=Count('id'),
        total_days=Sum('total_days'),
        avg_duration=Avg('total_days')
    ).order_by('-count')
    
    # Monthly trends
    monthly_trends = {}
    for month in range(1, 13):
        month_apps = applications.filter(start_date__month=month)
        monthly_trends[datetime(2000, month, 1).strftime('%B')] = {
            'applications': month_apps.count(),
            'approved': month_apps.filter(status='APPROVED').count(),
            'days_taken': sum([app.total_days for app in month_apps.filter(status='APPROVED')])
        }
    
    # Department-wise stats
    from employees.models import Department
    departments = Department.objects.all()
    dept_stats = []
    
    for dept in departments:
        dept_apps = applications.filter(employee__employee_profile__department=dept)
        dept_approved = dept_apps.filter(status='APPROVED')
        
        dept_stats.append({
            'department': dept.name,
            'total_applications': dept_apps.count(),
            'approved_applications': dept_approved.count(),
            'total_days_taken': sum([app.total_days for app in dept_approved]),
            'approval_rate': round((dept_approved.count() / dept_apps.count() * 100), 2) if dept_apps.count() > 0 else 0,
        })
    
    # Approval time analysis
    approved_apps = applications.filter(status='APPROVED', approved_on__isnull=False)
    approval_times = []
    for app in approved_apps:
        if app.approved_on and app.created_at:
            delta = (app.approved_on - app.created_at).days
            approval_times.append(delta)
    
    avg_approval_time = round(sum(approval_times) / len(approval_times), 2) if approval_times else 0
    
    # Most active leave takers
    top_leave_takers = User.objects.filter(
        role='EMPLOYEE',
        leave_applications__start_date__gte=start_date,
        leave_applications__end_date__lte=end_date,
        leave_applications__status='APPROVED'
    ).annotate(
        leave_count=Count('leave_applications'),
        total_days=Sum('leave_applications__total_days')
    ).order_by('-total_days')[:10]
    
    top_leave_takers_data = [{
        'employee_name': f"{emp.first_name} {emp.last_name}",
        'leave_applications': emp.leave_count,
        'total_days_taken': emp.total_days,
    } for emp in top_leave_takers]
    
    analytics = {
        'period': {
            'start_date': start_date,
            'end_date': end_date,
        },
        'overview': {
            'total_applications': applications.count(),
            'approved_applications': applications.filter(status='APPROVED').count(),
            'pending_applications': applications.filter(status='PENDING').count(),
            'rejection_rate': round((applications.filter(status='REJECTED').count() / applications.count() * 100), 2) if applications.count() > 0 else 0,
            'average_approval_time_days': avg_approval_time,
        },
        'status_distribution': list(status_distribution),
        'leave_type_analysis': list(leave_type_stats),
        'monthly_trends': monthly_trends,
        'department_analysis': dept_stats,
        'top_leave_takers': top_leave_takers_data,
    }
    
    return Response(analytics)

@api_view(['GET'])
@permission_classes([IsHRPermission])
def combined_performance_report(request):
    """Combined attendance and leave report for performance appraisal (HR only)"""
    employee_id = request.query_params.get('employee_id')
    year = request.query_params.get('year', date.today().year)
    
    if not employee_id:
        return Response(
            {'error': 'employee_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    employee = get_object_or_404(User, id=employee_id)
    year = int(year)
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    # Attendance metrics
    attendance_records = AttendanceRecord.objects.filter(
        employee=employee,
        date__gte=start_date,
        date__lte=end_date
    )
    
    total_days = (end_date - start_date).days + 1
    present_days = attendance_records.filter(status__in=['PRESENT', 'HALF_DAY']).count()
    late_days = attendance_records.filter(status='LATE').count()
    absent_days = attendance_records.filter(status='ABSENT').count()
    
    hours_stats = attendance_records.aggregate(
        total_hours=Sum('actual_hours'),
        total_overtime=Sum('overtime_hours'),
        avg_hours=Avg('actual_hours')
    )
    
    # Leave metrics
    leave_applications = LeaveApplication.objects.filter(
        employee=employee,
        start_date__gte=start_date,
        end_date__lte=end_date
    )
    
    approved_leaves = leave_applications.filter(status='APPROVED')
    total_leave_days = sum([app.total_days for app in approved_leaves])
    
    # Calculate performance scores
    attendance_score = round((present_days / total_days * 100), 2) if total_days > 0 else 0
    punctuality_score = round(((present_days - late_days) / present_days * 100), 2) if present_days > 0 else 0
    leave_planning_score = round((approved_leaves.count() / leave_applications.count() * 100), 2) if leave_applications.count() > 0 else 100
    
    # Overall performance score (weighted average)
    overall_score = round(
        (attendance_score * 0.4) + 
        (punctuality_score * 0.3) + 
        (leave_planning_score * 0.2) +
        (min((hours_stats['total_overtime'] or 0) / 100 * 10, 10) * 0.1),
        2
    )
    
    # Performance rating
    if overall_score >= 90:
        rating = 'Excellent'
    elif overall_score >= 80:
        rating = 'Very Good'
    elif overall_score >= 70:
        rating = 'Good'
    elif overall_score >= 60:
        rating = 'Satisfactory'
    else:
        rating = 'Needs Improvement'
    
    report = {
        'employee': {
            'id': employee.id,
            'name': f"{employee.first_name} {employee.last_name}",
            'email': employee.email,
            'department': employee.employee_profile.department.name if hasattr(employee, 'employee_profile') and employee.employee_profile.department else 'N/A',
        },
        'period': {
            'year': year,
            'start_date': start_date,
            'end_date': end_date,
        },
        'attendance_metrics': {
            'total_working_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'attendance_rate': attendance_score,
            'punctuality_rate': punctuality_score,
            'total_hours_worked': round(hours_stats['total_hours'] or 0, 2),
            'overtime_hours': round(hours_stats['total_overtime'] or 0, 2),
            'average_daily_hours': round(hours_stats['avg_hours'] or 0, 2),
        },
        'leave_metrics': {
            'total_leave_applications': leave_applications.count(),
            'approved_leaves': approved_leaves.count(),
            'rejected_leaves': leave_applications.filter(status='REJECTED').count(),
            'total_leave_days_taken': total_leave_days,
            'leave_planning_score': leave_planning_score,
        },
        'performance_summary': {
            'attendance_score': attendance_score,
            'punctuality_score': punctuality_score,
            'leave_planning_score': leave_planning_score,
            'overall_performance_score': overall_score,
            'performance_rating': rating,
        },
        'recommendations': generate_recommendations(
            attendance_score, 
            punctuality_score, 
            late_days, 
            absent_days,
            leave_planning_score
        )
    }
    
    return Response(report)

def generate_recommendations(attendance_score, punctuality_score, late_days, absent_days, leave_planning_score):
    """Generate performance recommendations"""
    recommendations = []
    
    if attendance_score < 70:
        recommendations.append({
            'category': 'Attendance',
            'severity': 'high',
            'message': f'Attendance rate is below expectations ({attendance_score}%). Focus on improving regular attendance.'
        })
    elif attendance_score < 85:
        recommendations.append({
            'category': 'Attendance',
            'severity': 'medium',
            'message': f'Attendance rate needs improvement ({attendance_score}%). Strive for more consistent attendance.'
        })
    
    if punctuality_score < 70:
        recommendations.append({
            'category': 'Punctuality',
            'severity': 'high',
            'message': f'Punctuality needs significant improvement ({punctuality_score}%). {late_days} late arrivals recorded.'
        })
    elif punctuality_score < 90:
        recommendations.append({
            'category': 'Punctuality',
            'severity': 'medium',
            'message': f'Work on improving punctuality ({punctuality_score}%). Reduce late arrivals.'
        })
    
    if absent_days > 10:
        recommendations.append({
            'category': 'Absenteeism',
            'severity': 'high',
            'message': f'High number of absences ({absent_days} days). Consider discussing with HR.'
        })
    
    if leave_planning_score < 80:
        recommendations.append({
            'category': 'Leave Planning',
            'severity': 'medium',
            'message': 'Improve leave planning. Apply for leaves well in advance and ensure proper documentation.'
        })
    
    if not recommendations:
        recommendations.append({
            'category': 'Overall',
            'severity': 'low',
            'message': 'Excellent performance! Keep up the good work.'
        })
    
    return recommendations
