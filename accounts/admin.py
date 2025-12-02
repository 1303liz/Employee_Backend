from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'employee_id', 'department', 'is_active')
    list_filter = ('role', 'department', 'is_active', 'hire_date')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_id')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Employee Information', {
            'fields': ('role', 'employee_id', 'department', 'phone_number', 'hire_date')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Employee Information', {
            'fields': ('role', 'employee_id', 'department', 'phone_number', 'hire_date')
        }),
    )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

admin.site.register(CustomUser, CustomUserAdmin)
