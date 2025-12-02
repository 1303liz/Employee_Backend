from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from datetime import date, timedelta

from .models import (
    WorkSchedule, EmployeeSchedule, AttendanceRecord, 
    BreakRecord, AttendancePolicy, Holiday
)

@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'start_time', 'end_time', 'work_duration_hours',
        'break_duration_minutes', 'working_days_display', 'is_active'
    ]
    list_filter = ['is_active', 'start_time', 'end_time']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Work Hours', {
            'fields': ('start_time', 'end_time')
        }),
        ('Break Configuration', {
            'fields': ('break_duration_minutes', 'max_break_sessions')
        }),
        ('Grace Periods', {
            'fields': ('late_grace_minutes', 'early_departure_grace_minutes')
        }),
        ('Working Days', {
            'fields': (
                ('monday', 'tuesday', 'wednesday'),
                ('thursday', 'friday'),
                ('saturday', 'sunday')
            )
        })
    )
    
    def working_days_display(self, obj):
        days = []
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        day_fields = [obj.monday, obj.tuesday, obj.wednesday, obj.thursday, obj.friday, obj.saturday, obj.sunday]
        
        for i, is_working in enumerate(day_fields):
            if is_working:
                days.append(day_names[i])
        return ', '.join(days) if days else 'No working days'
    working_days_display.short_description = 'Working Days'

@admin.register(EmployeeSchedule)
class EmployeeScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'schedule', 'start_date', 'end_date', 
        'effective_start_time', 'effective_end_time', 'is_active'
    ]
    list_filter = ['is_active', 'start_date', 'schedule']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name']
    
    fieldsets = (
        ('Assignment', {
            'fields': ('employee', 'schedule', 'is_active')
        }),
        ('Effective Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Custom Hours (Optional)', {
            'fields': ('custom_start_time', 'custom_end_time'),
            'classes': ('collapse',)
        })
    )

class BreakRecordInline(admin.TabularInline):
    model = BreakRecord
    extra = 0
    readonly_fields = ['duration']
    fields = ['break_type', 'start_time', 'end_time', 'duration', 'notes']

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'date', 'status_badge', 'check_in_time', 'check_out_time',
        'actual_hours', 'overtime_hours', 'late_indicator'
    ]
    list_filter = [
        'status', 'is_late', 'date', 'employee__department'
    ]
    search_fields = [
        'employee__username', 'employee__first_name', 'employee__last_name'
    ]
    date_hierarchy = 'date'
    inlines = [BreakRecordInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('employee', 'date')
        }),
        ('Time Tracking', {
            'fields': (
                ('check_in_time', 'check_out_time'),
                ('scheduled_hours', 'actual_hours', 'overtime_hours')
            )
        }),
        ('Break Information', {
            'fields': ('total_break_duration', 'break_sessions_count')
        }),
        ('Status Information', {
            'fields': ('status', 'is_late', 'is_early_departure')
        }),
        ('Location Tracking', {
            'fields': ('check_in_location', 'check_out_location'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        })
    )
    
    readonly_fields = ['actual_hours', 'overtime_hours']
    
    def status_badge(self, obj):
        colors = {
            'PRESENT': 'green',
            'ABSENT': 'red',
            'LATE': 'orange',
            'HALF_DAY': 'blue',
            'ON_LEAVE': 'purple',
            'HOLIDAY': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def late_indicator(self, obj):
        if obj.is_late:
            return format_html('<span style="color: red;">⚠ Late</span>')
        return format_html('<span style="color: green;">✓ On Time</span>')
    late_indicator.short_description = 'Punctuality'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee')

@admin.register(BreakRecord)
class BreakRecordAdmin(admin.ModelAdmin):
    list_display = [
        'employee_name', 'date', 'break_type', 'start_time', 'end_time', 'duration_display'
    ]
    list_filter = ['break_type', 'attendance_record__date']
    search_fields = [
        'attendance_record__employee__username',
        'attendance_record__employee__first_name',
        'attendance_record__employee__last_name'
    ]
    
    def employee_name(self, obj):
        return obj.attendance_record.employee.get_full_name()
    employee_name.short_description = 'Employee'
    
    def date(self, obj):
        return obj.attendance_record.date
    date.short_description = 'Date'
    
    def duration_display(self, obj):
        if obj.duration:
            minutes = obj.duration.total_seconds() / 60
            return f"{int(minutes)} min"
        return "-"
    duration_display.short_description = 'Duration'

@admin.register(AttendancePolicy)
class AttendancePolicyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'working_days_per_week', 'working_hours_per_day',
        'overtime_threshold_hours', 'is_active'
    ]
    list_filter = ['is_active']
    search_fields = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Work Week Configuration', {
            'fields': ('working_days_per_week', 'working_hours_per_day')
        }),
        ('Overtime Policies', {
            'fields': ('overtime_threshold_hours', 'overtime_multiplier')
        }),
        ('Punctuality Policies', {
            'fields': ('late_threshold_minutes', 'early_departure_threshold_minutes')
        }),
        ('Break Policies', {
            'fields': ('minimum_break_duration_minutes', 'maximum_break_duration_minutes')
        }),
        ('Absence Alerts', {
            'fields': ('consecutive_absence_alert_days', 'monthly_absence_alert_percentage')
        })
    )

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'is_optional']
    list_filter = ['is_optional', 'date']
    search_fields = ['name', 'description']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Holiday Information', {
            'fields': ('name', 'date', 'is_optional')
        }),
        ('Description', {
            'fields': ('description',)
        })
    )

# Custom admin actions
def mark_present(modeladmin, request, queryset):
    """Mark selected attendance records as present"""
    queryset.update(status='PRESENT')
mark_present.short_description = "Mark selected records as Present"

def mark_absent(modeladmin, request, queryset):
    """Mark selected attendance records as absent"""
    queryset.update(status='ABSENT')
mark_absent.short_description = "Mark selected records as Absent"

# Add actions to AttendanceRecordAdmin
AttendanceRecordAdmin.actions = [mark_present, mark_absent]
