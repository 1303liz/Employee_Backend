from django.contrib import admin
from .models import LeaveType, LeaveBalance, LeaveApplication, LeaveApplicationAttachment, LeaveApplicationComment

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_days_per_year', 'requires_approval', 'advance_notice_days', 'is_active', 'created_at')
    list_filter = ('requires_approval', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_editable = ('is_active', 'requires_approval')

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'year', 'total_allocated', 'used_days', 'pending_days', 'available_days')
    list_filter = ('leave_type', 'year')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    ordering = ('user', 'leave_type', 'year')
    readonly_fields = ('available_days',)
    
    def available_days(self, obj):
        return obj.available_days
    available_days.short_description = 'Available Days'

class LeaveApplicationAttachmentInline(admin.TabularInline):
    model = LeaveApplicationAttachment
    extra = 0
    readonly_fields = ('uploaded_at',)

class LeaveApplicationCommentInline(admin.TabularInline):
    model = LeaveApplicationComment
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'leave_type', 'start_date', 'end_date', 'total_days', 
        'status', 'priority', 'applied_on', 'approved_by'
    )
    list_filter = (
        'status', 'priority', 'leave_type', 'is_half_day', 
        'applied_on', 'start_date'
    )
    search_fields = (
        'employee__username', 'employee__first_name', 'employee__last_name',
        'reason', 'approval_comments'
    )
    ordering = ('-applied_on',)
    date_hierarchy = 'applied_on'
    
    fieldsets = (
        ('Employee & Leave Details', {
            'fields': (
                'employee', 'leave_type', 'start_date', 'end_date', 
                'total_days', 'is_half_day', 'reason', 'priority'
            )
        }),
        ('Contact Information', {
            'fields': ('contact_number', 'emergency_contact', 'replacement_employee')
        }),
        ('Application Status', {
            'fields': ('status', 'applied_on')
        }),
        ('Approval Information', {
            'fields': ('approved_by', 'approved_on', 'approval_comments')
        }),
    )
    
    readonly_fields = ('applied_on', 'approved_on')
    
    inlines = [LeaveApplicationAttachmentInline, LeaveApplicationCommentInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.employee = obj.employee or request.user
        super().save_model(request, obj, form, change)

@admin.register(LeaveApplicationAttachment)
class LeaveApplicationAttachmentAdmin(admin.ModelAdmin):
    list_display = ('leave_application', 'file_name', 'file_size', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('leave_application__employee__username', 'file_name')
    ordering = ('-uploaded_at',)

@admin.register(LeaveApplicationComment)
class LeaveApplicationCommentAdmin(admin.ModelAdmin):
    list_display = ('leave_application', 'author', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('leave_application__employee__username', 'comment', 'author__username')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # HR can see all comments, others only their own
        if not request.user.is_hr:
            qs = qs.filter(author=request.user)
        return qs
