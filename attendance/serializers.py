from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, date, timedelta
from .models import (
    WorkSchedule, EmployeeSchedule, AttendanceRecord, 
    BreakRecord, AttendancePolicy, Holiday
)
from accounts.serializers import UserSerializer

User = get_user_model()

class WorkScheduleSerializer(serializers.ModelSerializer):
    """Serializer for work schedules"""
    work_duration_hours = serializers.ReadOnlyField()
    
    class Meta:
        model = WorkSchedule
        fields = [
            'id', 'name', 'description', 'start_time', 'end_time',
            'break_duration_minutes', 'max_break_sessions',
            'late_grace_minutes', 'early_departure_grace_minutes',
            'monday', 'tuesday', 'wednesday', 'thursday',
            'friday', 'saturday', 'sunday', 'work_duration_hours',
            'is_active', 'created_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
        }

class EmployeeScheduleSerializer(serializers.ModelSerializer):
    """Serializer for employee schedules"""
    employee = UserSerializer(read_only=True)
    schedule = WorkScheduleSerializer(read_only=True)
    schedule_id = serializers.IntegerField(write_only=True)
    effective_start_time = serializers.ReadOnlyField()
    effective_end_time = serializers.ReadOnlyField()
    
    class Meta:
        model = EmployeeSchedule
        fields = [
            'id', 'employee', 'schedule', 'schedule_id', 'start_date', 'end_date',
            'custom_start_time', 'custom_end_time', 'effective_start_time',
            'effective_end_time', 'is_active', 'created_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
        }
    
    def create(self, validated_data):
        schedule_id = validated_data.pop('schedule_id')
        try:
            schedule = WorkSchedule.objects.get(id=schedule_id)
            return EmployeeSchedule.objects.create(
                schedule=schedule,
                **validated_data
            )
        except WorkSchedule.DoesNotExist:
            raise serializers.ValidationError({'schedule_id': 'Invalid schedule ID'})

class BreakRecordSerializer(serializers.ModelSerializer):
    """Serializer for break records"""
    break_type_display = serializers.CharField(source='get_break_type_display', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = BreakRecord
        fields = [
            'id', 'break_type', 'break_type_display', 'start_time', 'end_time',
            'duration', 'duration_minutes', 'notes', 'created_at'
        ]
        extra_kwargs = {
            'duration': {'read_only': True},
            'created_at': {'read_only': True},
        }
    
    def get_duration_minutes(self, obj):
        if obj.duration:
            return obj.duration.total_seconds() / 60
        return 0

class AttendanceRecordDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for attendance records"""
    employee = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    break_records = BreakRecordSerializer(many=True, read_only=True)
    
    # Calculated fields
    total_break_minutes = serializers.SerializerMethodField()
    is_checked_in = serializers.SerializerMethodField()
    work_duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'employee', 'date', 'check_in_time', 'check_out_time',
            'total_break_duration', 'total_break_minutes', 'break_sessions_count',
            'status', 'status_display', 'is_late', 'is_early_departure',
            'scheduled_hours', 'actual_hours', 'overtime_hours',
            'check_in_location', 'check_out_location', 'notes',
            'break_records', 'is_checked_in', 'work_duration_display',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'actual_hours': {'read_only': True},
            'overtime_hours': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }
    
    def get_total_break_minutes(self, obj):
        return obj.total_break_duration.total_seconds() / 60
    
    def get_is_checked_in(self, obj):
        return obj.check_in_time is not None and obj.check_out_time is None
    
    def get_work_duration_display(self, obj):
        if obj.actual_hours:
            hours = int(obj.actual_hours)
            minutes = int((obj.actual_hours % 1) * 60)
            return f"{hours}h {minutes}m"
        return "0h 0m"

class AttendanceRecordListSerializer(serializers.ModelSerializer):
    """List serializer for attendance records"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_checked_in = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'employee_name', 'date', 'check_in_time', 'check_out_time',
            'status', 'status_display', 'is_late', 'actual_hours', 'overtime_hours',
            'is_checked_in'
        ]
    
    def get_is_checked_in(self, obj):
        return obj.check_in_time is not None and obj.check_out_time is None

class CheckInSerializer(serializers.Serializer):
    """Serializer for employee check-in"""
    latitude = serializers.FloatField(required=True)
    longitude = serializers.FloatField(required=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate location coordinates"""
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is None or longitude is None:
            raise serializers.ValidationError('Location coordinates are required for check-in.')
        
        # Validate coordinate ranges
        if not (-90 <= latitude <= 90):
            raise serializers.ValidationError('Invalid latitude. Must be between -90 and 90.')
        
        if not (-180 <= longitude <= 180):
            raise serializers.ValidationError('Invalid longitude. Must be between -180 and 180.')
        
        # Optional: Check if location is within allowed workplace radius
        # This can be implemented with WORKPLACE_COORDINATES from settings
        from django.conf import settings
        if hasattr(settings, 'WORKPLACE_COORDINATES') and hasattr(settings, 'ALLOWED_RADIUS_METERS'):
            from math import radians, sin, cos, sqrt, atan2
            
            workplace_lat = settings.WORKPLACE_COORDINATES['latitude']
            workplace_lon = settings.WORKPLACE_COORDINATES['longitude']
            allowed_radius = settings.ALLOWED_RADIUS_METERS
            
            # Calculate distance using Haversine formula
            R = 6371000  # Earth's radius in meters
            lat1, lon1 = radians(workplace_lat), radians(workplace_lon)
            lat2, lon2 = radians(latitude), radians(longitude)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            if distance > allowed_radius:
                raise serializers.ValidationError(
                    f'You are {int(distance)} meters away from the workplace. '
                    f'You must be within {allowed_radius} meters to check in.'
                )
        
        return data
    
    def create(self, validated_data):
        from decimal import Decimal
        
        employee = self.context['request'].user
        today = date.today()
        latitude = validated_data.get('latitude')
        longitude = validated_data.get('longitude')
        location = validated_data.get('location', f'{latitude}, {longitude}')
        notes = validated_data.get('notes', '')
        
        try:
            # Check if already checked in today
            attendance, created = AttendanceRecord.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={
                    'check_in_time': timezone.now(),
                    'check_in_location': location,
                    'notes': notes,
                    'scheduled_hours': Decimal('8.0'),  # Default, can be customized
                }
            )
            
            if not created and attendance.check_in_time:
                raise serializers.ValidationError('Already checked in today.')
            
            if not created:
                attendance.check_in_time = timezone.now()
                attendance.check_in_location = location
                attendance.notes = notes
                attendance.save()
            
            return attendance
        except Exception as e:
            raise serializers.ValidationError(f'Check-in failed: {str(e)}')

class CheckOutSerializer(serializers.Serializer):
    """Serializer for employee check-out"""
    latitude = serializers.FloatField(required=True)
    longitude = serializers.FloatField(required=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate location coordinates"""
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is None or longitude is None:
            raise serializers.ValidationError('Location coordinates are required for check-out.')
        
        # Validate coordinate ranges
        if not (-90 <= latitude <= 90):
            raise serializers.ValidationError('Invalid latitude. Must be between -90 and 90.')
        
        if not (-180 <= longitude <= 180):
            raise serializers.ValidationError('Invalid longitude. Must be between -180 and 180.')
        
        return data
    
    def create(self, validated_data):
        employee = self.context['request'].user
        today = date.today()
        latitude = validated_data.get('latitude')
        longitude = validated_data.get('longitude')
        location = validated_data.get('location', f'{latitude}, {longitude}')
        notes = validated_data.get('notes', '')
        
        try:
            attendance = AttendanceRecord.objects.get(
                employee=employee,
                date=today
            )
        except AttendanceRecord.DoesNotExist:
            raise serializers.ValidationError('No check-in record found for today.')
        
        if not attendance.check_in_time:
            raise serializers.ValidationError('Must check in before checking out.')
        
        if attendance.check_out_time:
            raise serializers.ValidationError('Already checked out today.')
        
        attendance.check_out_time = timezone.now()
        attendance.check_out_location = location
        if notes:
            attendance.notes = f"{attendance.notes}\n{notes}" if attendance.notes else notes
        
        try:
            attendance.save()
        except Exception as e:
            raise serializers.ValidationError(f'Check-out failed: {str(e)}')
        
        return attendance

class BreakStartSerializer(serializers.Serializer):
    """Serializer for starting a break"""
    break_type = serializers.ChoiceField(choices=BreakRecord.BREAK_TYPE_CHOICES)
    notes = serializers.CharField(max_length=200, required=False, allow_blank=True)
    
    def create(self, validated_data):
        employee = self.context['request'].user
        today = date.today()
        
        try:
            attendance = AttendanceRecord.objects.get(
                employee=employee,
                date=today,
                check_in_time__isnull=False,
                check_out_time__isnull=True
            )
        except AttendanceRecord.DoesNotExist:
            raise serializers.ValidationError('Must be checked in to start a break.')
        
        # Check for ongoing break
        ongoing_break = BreakRecord.objects.filter(
            attendance_record=attendance,
            end_time__isnull=True
        ).first()
        
        if ongoing_break:
            raise serializers.ValidationError('Already on a break. End current break first.')
        
        break_record = BreakRecord.objects.create(
            attendance_record=attendance,
            break_type=validated_data['break_type'],
            start_time=timezone.now(),
            notes=validated_data.get('notes', '')
        )
        
        return break_record

class BreakEndSerializer(serializers.Serializer):
    """Serializer for ending a break"""
    
    def create(self, validated_data):
        employee = self.context['request'].user
        today = date.today()
        
        try:
            attendance = AttendanceRecord.objects.get(
                employee=employee,
                date=today,
                check_in_time__isnull=False
            )
        except AttendanceRecord.DoesNotExist:
            raise serializers.ValidationError('No attendance record found for today.')
        
        # Find ongoing break
        ongoing_break = BreakRecord.objects.filter(
            attendance_record=attendance,
            end_time__isnull=True
        ).first()
        
        if not ongoing_break:
            raise serializers.ValidationError('No ongoing break found.')
        
        ongoing_break.end_time = timezone.now()
        ongoing_break.save()
        
        return ongoing_break

class AttendancePolicySerializer(serializers.ModelSerializer):
    """Serializer for attendance policies"""
    
    class Meta:
        model = AttendancePolicy
        fields = [
            'id', 'name', 'description', 'working_days_per_week',
            'working_hours_per_day', 'overtime_threshold_hours',
            'overtime_multiplier', 'late_threshold_minutes',
            'early_departure_threshold_minutes', 'minimum_break_duration_minutes',
            'maximum_break_duration_minutes', 'consecutive_absence_alert_days',
            'monthly_absence_alert_percentage', 'is_active', 'created_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
        }

class HolidaySerializer(serializers.ModelSerializer):
    """Serializer for holidays"""
    
    class Meta:
        model = Holiday
        fields = [
            'id', 'name', 'date', 'description', 'is_optional', 'created_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
        }

class AttendanceReportSerializer(serializers.Serializer):
    """Serializer for attendance reports"""
    employee_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    report_type = serializers.ChoiceField(
        choices=[
            ('DAILY', 'Daily Report'),
            ('WEEKLY', 'Weekly Report'),
            ('MONTHLY', 'Monthly Report'),
            ('SUMMARY', 'Summary Report'),
        ]
    )
    
    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError('End date must be after start date.')
        return data