from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Sum, Avg
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, date, timedelta

from .models import (
    WorkSchedule, EmployeeSchedule, AttendanceRecord, 
    BreakRecord, AttendancePolicy, Holiday
)
from .serializers import (
    WorkScheduleSerializer, EmployeeScheduleSerializer, 
    AttendanceRecordDetailSerializer, AttendanceRecordListSerializer,
    CheckInSerializer, CheckOutSerializer, BreakStartSerializer, BreakEndSerializer,
    BreakRecordSerializer, AttendancePolicySerializer, HolidaySerializer,
    AttendanceReportSerializer
)
from accounts.views import IsHRPermission

User = get_user_model()

# Employee Check-in/Check-out

class CheckInAPIView(APIView):
    """Employee check-in"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CheckInSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            attendance = serializer.save()
            return Response(
                AttendanceRecordDetailSerializer(attendance, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckOutAPIView(APIView):
    """Employee check-out"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CheckOutSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            attendance = serializer.save()
            return Response(
                AttendanceRecordDetailSerializer(attendance, context={'request': request}).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BreakStartAPIView(APIView):
    """Start a break"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = BreakStartSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            break_record = serializer.save()
            return Response(
                BreakRecordSerializer(break_record).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BreakEndAPIView(APIView):
    """End a break"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = BreakEndSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            break_record = serializer.save()
            return Response(
                BreakRecordSerializer(break_record).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Attendance Records

class AttendanceRecordListAPIView(generics.ListAPIView):
    """List attendance records"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_hr:
            # HR can see all attendance records
            queryset = AttendanceRecord.objects.select_related('employee').all()
        else:
            # Employees can only see their own records
            queryset = AttendanceRecord.objects.filter(employee=user)
        
        # Filter parameters
        employee_id = self.request.query_params.get('employee')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        status_filter = self.request.query_params.get('status')
        
        if employee_id and user.is_hr:
            queryset = queryset.filter(employee_id=employee_id)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-date')
    
    def get_serializer_class(self):
        if self.request.query_params.get('detailed') == 'true':
            return AttendanceRecordDetailSerializer
        return AttendanceRecordListSerializer

class AttendanceRecordDetailAPIView(generics.RetrieveUpdateAPIView):
    """Retrieve or update attendance record"""
    serializer_class = AttendanceRecordDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_hr:
            return AttendanceRecord.objects.select_related('employee').prefetch_related('break_records')
        else:
            return AttendanceRecord.objects.filter(employee=user).prefetch_related('break_records')

class MyTodayAttendanceAPIView(APIView):
    """Get current user's today attendance"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        today = date.today()
        try:
            attendance = AttendanceRecord.objects.prefetch_related('break_records').get(
                employee=request.user,
                date=today
            )
            serializer = AttendanceRecordDetailSerializer(attendance, context={'request': request})
            return Response(serializer.data)
        except AttendanceRecord.DoesNotExist:
            return Response({
                'message': 'No attendance record for today',
                'date': today,
                'is_checked_in': False
            }, status=status.HTTP_404_NOT_FOUND)

class MyAttendanceHistoryAPIView(generics.ListAPIView):
    """Get current user's attendance history"""
    serializer_class = AttendanceRecordListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        days = int(self.request.query_params.get('days', 30))
        start_date = date.today() - timedelta(days=days)
        
        return AttendanceRecord.objects.filter(
            employee=self.request.user,
            date__gte=start_date
        ).order_by('-date')

# Schedule Management

class WorkScheduleListCreateAPIView(generics.ListCreateAPIView):
    """List or create work schedules (HR only for creation)"""
    queryset = WorkSchedule.objects.filter(is_active=True).order_by('name')
    serializer_class = WorkScheduleSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsHRPermission()]
        return [permissions.IsAuthenticated()]

class EmployeeScheduleListCreateAPIView(generics.ListCreateAPIView):
    """List or create employee schedules (HR only)"""
    serializer_class = EmployeeScheduleSerializer
    permission_classes = [IsHRPermission]
    
    def get_queryset(self):
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            return EmployeeSchedule.objects.select_related(
                'employee', 'schedule'
            ).filter(employee_id=employee_id)
        return EmployeeSchedule.objects.select_related(
            'employee', 'schedule'
        ).filter(is_active=True)
    
    def perform_create(self, serializer):
        employee_id = self.request.data.get('employee_id')
        if employee_id:
            try:
                employee = User.objects.get(id=employee_id)
                serializer.save(employee=employee)
            except User.DoesNotExist:
                raise serializers.ValidationError({'employee_id': 'Invalid employee ID'})
        else:
            raise serializers.ValidationError({'employee_id': 'Employee ID is required'})

# Policy and Holiday Management

class AttendancePolicyListCreateAPIView(generics.ListCreateAPIView):
    """List or create attendance policies (HR only for creation)"""
    queryset = AttendancePolicy.objects.filter(is_active=True)
    serializer_class = AttendancePolicySerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsHRPermission()]
        return [permissions.IsAuthenticated()]

class HolidayListCreateAPIView(generics.ListCreateAPIView):
    """List or create holidays (HR only for creation)"""
    serializer_class = HolidaySerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsHRPermission()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        year = self.request.query_params.get('year', date.today().year)
        return Holiday.objects.filter(date__year=year).order_by('date')

# Reports and Statistics

@api_view(['GET'])
@permission_classes([IsHRPermission])
def attendance_statistics(request):
    """Get comprehensive attendance statistics"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not start_date or not end_date:
        # Default to current month
        today = date.today()
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Overall statistics
    total_records = AttendanceRecord.objects.filter(
        date__range=[start_date, end_date]
    )
    
    present_count = total_records.filter(status='PRESENT').count()
    absent_count = total_records.filter(status='ABSENT').count()
    late_count = total_records.filter(is_late=True).count()
    
    # Average working hours
    avg_working_hours = total_records.aggregate(
        avg_hours=Avg('actual_hours')
    )['avg_hours'] or 0
    
    # Total overtime
    total_overtime = total_records.aggregate(
        total_overtime=Sum('overtime_hours')
    )['total_overtime'] or 0
    
    # Department-wise statistics
    dept_stats = total_records.values(
        'employee__department'
    ).annotate(
        total_employees=Count('employee', distinct=True),
        present_days=Count('id', filter=Q(status='PRESENT')),
        absent_days=Count('id', filter=Q(status='ABSENT')),
        avg_hours=Avg('actual_hours')
    ).order_by('employee__department')
    
    # Daily attendance trend
    daily_trend = []
    current_date = start_date
    while current_date <= end_date:
        daily_count = total_records.filter(date=current_date, status='PRESENT').count()
        daily_trend.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'present_count': daily_count
        })
        current_date += timedelta(days=1)
    
    # Top performers (most punctual)
    top_performers = total_records.values(
        'employee__username',
        'employee__first_name',
        'employee__last_name'
    ).annotate(
        total_days=Count('id'),
        on_time_days=Count('id', filter=Q(is_late=False)),
        avg_hours=Avg('actual_hours'),
        total_overtime=Sum('overtime_hours')
    ).order_by('-on_time_days')[:10]
    
    stats = {
        'summary': {
            'total_records': total_records.count(),
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'average_working_hours': round(avg_working_hours, 2),
            'total_overtime_hours': round(total_overtime, 2),
        },
        'department_statistics': list(dept_stats),
        'daily_trend': daily_trend,
        'top_performers': list(top_performers),
        'period': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
    }
    
    return Response(stats)

@api_view(['POST'])
@permission_classes([IsHRPermission])
def generate_attendance_report(request):
    """Generate attendance report"""
    serializer = AttendanceReportSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        
        # Base queryset
        queryset = AttendanceRecord.objects.select_related('employee').filter(
            date__range=[data['start_date'], data['end_date']]
        )
        
        if data.get('employee_id'):
            queryset = queryset.filter(employee_id=data['employee_id'])
        
        # Generate report based on type
        report_type = data['report_type']
        
        if report_type == 'DAILY':
            report_data = queryset.order_by('date', 'employee__username')
            serialized_data = AttendanceRecordListSerializer(report_data, many=True).data
        
        elif report_type == 'SUMMARY':
            # Employee-wise summary
            summary = queryset.values(
                'employee__username',
                'employee__first_name',
                'employee__last_name'
            ).annotate(
                total_days=Count('id'),
                present_days=Count('id', filter=Q(status='PRESENT')),
                absent_days=Count('id', filter=Q(status='ABSENT')),
                late_days=Count('id', filter=Q(is_late=True)),
                total_hours=Sum('actual_hours'),
                overtime_hours=Sum('overtime_hours'),
                avg_daily_hours=Avg('actual_hours')
            ).order_by('employee__username')
            
            serialized_data = list(summary)
        
        else:
            # Default to list format
            serialized_data = AttendanceRecordListSerializer(queryset, many=True).data
        
        return Response({
            'report_type': report_type,
            'period': {
                'start_date': data['start_date'],
                'end_date': data['end_date']
            },
            'data': serialized_data,
            'total_records': queryset.count()
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_attendance_summary(request):
    """Get current user's attendance summary"""
    user = request.user
    days = int(request.query_params.get('days', 30))
    start_date = date.today() - timedelta(days=days)
    
    records = AttendanceRecord.objects.filter(
        employee=user,
        date__gte=start_date
    )
    
    # Calculate summary
    total_days = records.count()
    present_days = records.filter(status='PRESENT').count()
    absent_days = records.filter(status='ABSENT').count()
    late_days = records.filter(is_late=True).count()
    
    # Working hours summary
    total_hours = records.aggregate(Sum('actual_hours'))['actual_hours__sum'] or 0
    overtime_hours = records.aggregate(Sum('overtime_hours'))['overtime_hours__sum'] or 0
    avg_daily_hours = records.aggregate(Avg('actual_hours'))['actual_hours__avg'] or 0
    
    # Recent attendance
    recent_records = records.order_by('-date')[:7]
    recent_data = AttendanceRecordListSerializer(recent_records, many=True).data
    
    # Today's status
    today = date.today()
    today_record = records.filter(date=today).first()
    today_status = {
        'date': today,
        'is_checked_in': False,
        'check_in_time': None,
        'check_out_time': None,
        'status': 'Not Started'
    }
    
    if today_record:
        today_status = {
            'date': today,
            'is_checked_in': today_record.check_in_time is not None and today_record.check_out_time is None,
            'check_in_time': today_record.check_in_time,
            'check_out_time': today_record.check_out_time,
            'status': today_record.get_status_display()
        }
    
    summary = {
        'period_summary': {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'attendance_percentage': (present_days / total_days * 100) if total_days > 0 else 0,
        },
        'hours_summary': {
            'total_hours': round(total_hours, 2),
            'overtime_hours': round(overtime_hours, 2),
            'average_daily_hours': round(avg_daily_hours, 2),
        },
        'today_status': today_status,
        'recent_attendance': recent_data,
    }
    
    return Response(summary)
