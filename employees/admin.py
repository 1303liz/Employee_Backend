from django.contrib import admin
from .models import Position, EmployeeProfile, EmployeeDocument, EmployeeNote

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'created_at')
    list_filter = ('level', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('level', 'title')

class EmployeeDocumentInline(admin.TabularInline):
    model = EmployeeDocument
    extra = 0
    readonly_fields = ('uploaded_at',)

class EmployeeNoteInline(admin.TabularInline):
    model = EmployeeNote
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'position', 'employment_type', 'status', 
        'supervisor', 'created_at'
    )
    list_filter = (
        'employment_type', 'status', 'position', 'gender', 
        'user__department', 'created_at'
    )
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name', 
        'user__email', 'user__employee_id'
    )
    ordering = ('user__last_name', 'user__first_name')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'position', 'supervisor')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'gender', 'address')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Employment Details', {
            'fields': (
                'employment_type', 'status', 'salary', 'termination_date'
            )
        }),
    )
    
    inlines = [EmployeeDocumentInline, EmployeeNoteInline]
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'document_type', 'title', 'uploaded_by', 'uploaded_at'
    )
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('employee__user__first_name', 'employee__user__last_name', 'title')
    ordering = ('-uploaded_at',)

@admin.register(EmployeeNote)
class EmployeeNoteAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'note_type', 'author', 'is_confidential', 'created_at'
    )
    list_filter = ('note_type', 'is_confidential', 'created_at')
    search_fields = ('employee__user__first_name', 'employee__user__last_name', 'note')
    ordering = ('-created_at',)