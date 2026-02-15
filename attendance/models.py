from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, date, time, timedelta

User = get_user_model()

class WorkSchedule(models.Model):
    """Work schedules/shifts for employees"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    # Work hours
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Break configuration
    break_duration_minutes = models.PositiveIntegerField(default=60)
    max_break_sessions = models.PositiveIntegerField(default=2)
    
    # Grace periods
    late_grace_minutes = models.PositiveIntegerField(default=15)
    early_departure_grace_minutes = models.PositiveIntegerField(default=15)
    
    # Working days
    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"
    
    @property
    def work_duration_hours(self):
        """Calculate total work hours per day"""
        start_datetime = datetime.combine(date.today(), self.start_time)
        end_datetime = datetime.combine(date.today(), self.end_time)
        
        # Handle overnight shifts
        if self.end_time < self.start_time:
            end_datetime += timedelta(days=1)
        
        duration = end_datetime - start_datetime
        break_time = timedelta(minutes=self.break_duration_minutes)
        return (duration - break_time).total_seconds() / 3600
    
    def is_working_day(self, day_of_week):
        """Check if given day (0=Monday, 6=Sunday) is a working day"""
        working_days = [
            self.monday, self.tuesday, self.wednesday, self.thursday,
            self.friday, self.saturday, self.sunday
        ]
        return working_days[day_of_week] if 0 <= day_of_week <= 6 else False

class EmployeeSchedule(models.Model):
    """Assign schedules to employees"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    schedule = models.ForeignKey(WorkSchedule, on_delete=models.CASCADE)
    
    # Effective dates
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Override settings for specific employee
    custom_start_time = models.TimeField(null=True, blank=True)
    custom_end_time = models.TimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
        unique_together = ['employee', 'start_date']
    
    def __str__(self):
        return f"{self.employee.username} - {self.schedule.name} (from {self.start_date})"
    
    @property
    def effective_start_time(self):
        return self.custom_start_time or self.schedule.start_time
    
    @property
    def effective_end_time(self):
        return self.custom_end_time or self.schedule.end_time

class AttendanceRecord(models.Model):
    """Daily attendance records for employees"""
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('HALF_DAY', 'Half Day'),
        ('ON_LEAVE', 'On Leave'),
        ('HOLIDAY', 'Holiday'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    
    # Check-in/out times
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    
    # Break tracking
    total_break_duration = models.DurationField(default=timedelta(0))
    break_sessions_count = models.PositiveIntegerField(default=0)
    
    # Status and calculations
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ABSENT')
    is_late = models.BooleanField(default=False)
    is_early_departure = models.BooleanField(default=False)
    
    # Working hours
    scheduled_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8.0)
    actual_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    
    # Location tracking (optional)
    check_in_location = models.CharField(max_length=200, blank=True)
    check_out_location = models.CharField(max_length=200, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date', 'employee']
    
    def __str__(self):
        return f"{self.employee.username} - {self.date} ({self.get_status_display()})"
    
    def calculate_hours(self):
        """Calculate actual working hours"""
        from decimal import Decimal
        
        if self.check_in_time and self.check_out_time:
            total_time = self.check_out_time - self.check_in_time
            working_time = total_time - self.total_break_duration
            
            # Convert to hours - ensure Decimal type throughout
            hours = Decimal(str(working_time.total_seconds())) / Decimal('3600')
            self.actual_hours = Decimal(str(round(float(hours), 2)))
            
            # Ensure scheduled_hours is a Decimal
            if not isinstance(self.scheduled_hours, Decimal):
                self.scheduled_hours = Decimal(str(self.scheduled_hours))
            
            # Calculate overtime (hours beyond scheduled)
            if self.actual_hours > self.scheduled_hours:
                self.overtime_hours = self.actual_hours - self.scheduled_hours
            else:
                self.overtime_hours = Decimal('0')
        else:
            self.actual_hours = Decimal('0')
            self.overtime_hours = Decimal('0')
    
    def save(self, *args, **kwargs):
        from decimal import Decimal
        
        # Ensure scheduled_hours is Decimal before any calculations
        if not isinstance(self.scheduled_hours, Decimal):
            self.scheduled_hours = Decimal(str(self.scheduled_hours))
        
        self.calculate_hours()
        
        # Determine status based on times
        if self.check_in_time and not self.check_out_time:
            self.status = 'PRESENT'
        elif self.check_in_time and self.check_out_time:
            # Ensure actual_hours is Decimal for comparison
            if not isinstance(self.actual_hours, Decimal):
                self.actual_hours = Decimal(str(self.actual_hours))
            
            if self.actual_hours < (self.scheduled_hours * Decimal('0.5')):
                self.status = 'HALF_DAY'
            else:
                self.status = 'PRESENT'
        
        super().save(*args, **kwargs)

class BreakRecord(models.Model):
    """Break session records"""
    BREAK_TYPE_CHOICES = [
        ('LUNCH', 'Lunch Break'),
        ('TEA', 'Tea Break'),
        ('PERSONAL', 'Personal Break'),
        ('MEETING', 'Meeting Break'),
        ('OTHER', 'Other'),
    ]
    
    attendance_record = models.ForeignKey(
        AttendanceRecord, on_delete=models.CASCADE, 
        related_name='break_records'
    )
    break_type = models.CharField(max_length=10, choices=BREAK_TYPE_CHOICES, default='OTHER')
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    
    notes = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.attendance_record.employee.username} - {self.get_break_type_display()} on {self.start_time.date()}"
    
    def calculate_duration(self):
        """Calculate break duration"""
        if self.start_time and self.end_time:
            self.duration = self.end_time - self.start_time
            return self.duration
        return timedelta(0)
    
    def save(self, *args, **kwargs):
        if self.end_time:
            self.duration = self.calculate_duration()
        super().save(*args, **kwargs)
        
        # Update parent attendance record
        if self.attendance_record_id:
            self.update_attendance_record()
    
    def update_attendance_record(self):
        """Update parent attendance record with break totals"""
        attendance = self.attendance_record
        total_breaks = BreakRecord.objects.filter(
            attendance_record=attendance,
            end_time__isnull=False
        )
        
        total_duration = sum(
            (break_record.duration for break_record in total_breaks),
            timedelta(0)
        )
        
        attendance.total_break_duration = total_duration
        attendance.break_sessions_count = total_breaks.count()
        attendance.save()

class AttendancePolicy(models.Model):
    """Company attendance policies"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Work week configuration
    working_days_per_week = models.PositiveIntegerField(default=5)
    working_hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8.0)
    
    # Overtime policies
    overtime_threshold_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8.0)
    overtime_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.5)
    
    # Late/Early policies
    late_threshold_minutes = models.PositiveIntegerField(default=15)
    early_departure_threshold_minutes = models.PositiveIntegerField(default=15)
    
    # Break policies
    minimum_break_duration_minutes = models.PositiveIntegerField(default=30)
    maximum_break_duration_minutes = models.PositiveIntegerField(default=90)
    
    # Absence policies
    consecutive_absence_alert_days = models.PositiveIntegerField(default=3)
    monthly_absence_alert_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Attendance Policies'
    
    def __str__(self):
        return self.name

class Holiday(models.Model):
    """Company holidays"""
    name = models.CharField(max_length=100)
    date = models.DateField()
    description = models.TextField(blank=True)
    is_optional = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'date']
        ordering = ['date']
    
    def __str__(self):
        return f"{self.name} ({self.date})"
