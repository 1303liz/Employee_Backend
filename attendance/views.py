from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Avg, Sum
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
    CheckInSerializer, CheckOutSerializer, BreakRecordSerializer,
    AttendancePolicySerializer, HolidaySerializer
)
from accounts.views import IsHRPermission

User = get_user_model()


# Work Schedule Views
class WorkScheduleListCreateAPIView(generics.ListCreateAPIView):
    """List all work schedules or create a new one (HR only)"""
    queryset = WorkSchedule.objects.all()
    serializer_class = WorkScheduleSerializer
    permission_classes = [IsHRPermission]


class WorkScheduleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a work schedule (HR only)"""
    queryset = WorkSchedule.objects.all()
    serializer_class = WorkScheduleSerializer
    permission_classes = [IsHRPermission]


# Employee Schedule Views
class EmployeeScheduleListCreateAPIView(generics.ListCreateAPIView):
    """List all employee schedules or create a new one (HR only)"""
    serializer_class = EmployeeScheduleSerializer
    permission_classes = [IsHRPermission]
    
    def get_queryset(self):
        queryset = EmployeeSchedule.objects.select_related('employee', 'schedule').all()
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        return queryset.order_by('-start_date')


class EmployeeScheduleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete an employee schedule (HR only)"""
    queryset = EmployeeSchedule.objects.select_related('employee', 'schedule').all()
    serializer_class = EmployeeScheduleSerializer
    permission_classes = [IsHRPermission]


# Attendance Record Views
class AttendanceRecordListAPIView(generics.ListAPIView):
    """List attendance records"""
    serializer_class = AttendanceRecordListSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = AttendanceRecord.objects.select_related('employee').all()
        
        # HR can see all records, employees only their own
        if user.role != 'HR':
            queryset = queryset.filter(employee=user)
        
        # Filter parameters
        employee_id = self.request.query_params.get('employee_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        status_filter = self.request.query_params.get('status')
        
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-date', '-check_in_time')


class AttendanceRecordDetailAPIView(generics.RetrieveAPIView):
    """Retrieve a specific attendance record"""
    serializer_class = AttendanceRecordDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = AttendanceRecord.objects.select_related('employee').prefetch_related('break_records').all()
        
        # HR can see all records, employees only their own
        if user.role != 'HR':
            queryset = queryset.filter(employee=user)
        
        return queryset


# Check-in/Check-out Views
class CheckInAPIView(APIView):
    """Employee check-in endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CheckInSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            attendance_record = serializer.save()
            detail_serializer = AttendanceRecordDetailSerializer(attendance_record)
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckOutAPIView(APIView):
    """Employee check-out endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CheckOutSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            attendance_record = serializer.save()
            detail_serializer = AttendanceRecordDetailSerializer(attendance_record)
            return Response(detail_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Current Status View
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_attendance_status(request):
    """Get current user's attendance status for today"""
    today = date.today()
    try:
        record = AttendanceRecord.objects.select_related('employee').prefetch_related('break_records').get(
            employee=request.user,
            date=today
        )
        serializer = AttendanceRecordDetailSerializer(record)
        return Response(serializer.data)
    except AttendanceRecord.DoesNotExist:
        return Response({
            'message': 'No attendance record for today',
            'is_checked_in': False
        }, status=status.HTTP_200_OK)


# Dashboard/Statistics Views
@api_view(['GET'])
@permission_classes([IsHRPermission])
def attendance_dashboard(request):
    """Get attendance dashboard statistics"""
    today = date.today()
    
    # Today's statistics
    today_records = AttendanceRecord.objects.filter(date=today)
    total_employees = User.objects.filter(role='EMPLOYEE', is_active=True).count()
    present_count = today_records.filter(status='PRESENT').count()
    absent_count = today_records.filter(status='ABSENT').count()
    late_count = today_records.filter(is_late=True).count()
    
    # This month's statistics
    month_start = today.replace(day=1)
    month_records = AttendanceRecord.objects.filter(date__gte=month_start, date__lte=today)
    avg_attendance = month_records.filter(status='PRESENT').count()
    
    return Response({
        'today': {
            'total_employees': total_employees,
            'present': present_count,
            'absent': absent_count,
            'late': late_count,
            'on_leave': 0,  # This would need integration with leave module
        },
        'this_month': {
            'total_working_days': (today - month_start).days + 1,
            'average_attendance': avg_attendance,
        }
    })


# Holiday Views
class HolidayListCreateAPIView(generics.ListCreateAPIView):
    """List all holidays or create a new one (HR only)"""
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [IsHRPermission]


class HolidayDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a holiday (HR only)"""
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [IsHRPermission]
