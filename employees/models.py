from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

User = get_user_model()

class Position(models.Model):
    """Job positions within the company"""
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=50, choices=[
        ('INTERN', 'Intern'),
        ('JUNIOR', 'Junior'),
        ('SENIOR', 'Senior'),
        ('LEAD', 'Lead'),
        ('MANAGER', 'Manager'),
        ('DIRECTOR', 'Director'),
    ], default='JUNIOR')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['level', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.get_level_display()})"

class EmployeeProfile(models.Model):
    """Extended employee profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=[
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
        ('PREFER_NOT_TO_SAY', 'Prefer not to say'),
    ], blank=True)
    
    # Contact Information
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    # Employment Details
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    employment_type = models.CharField(max_length=20, choices=[
        ('FULL_TIME', 'Full-time'),
        ('PART_TIME', 'Part-time'),
        ('CONTRACT', 'Contract'),
        ('INTERN', 'Intern'),
    ], default='FULL_TIME')
    
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE', 'Active'),
        ('ON_LEAVE', 'On Leave'),
        ('TERMINATED', 'Terminated'),
        ('RESIGNED', 'Resigned'),
    ], default='ACTIVE')
    
    # Supervisor relationship
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='supervised_employees')
    
    # Dates
    termination_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.position or 'No Position'}"
    
    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def is_active_employee(self):
        return self.status == 'ACTIVE' and self.user.is_active

class EmployeeDocument(models.Model):
    """Documents related to employees"""
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=[
        ('RESUME', 'Resume'),
        ('CONTRACT', 'Employment Contract'),
        ('ID_COPY', 'ID Copy'),
        ('CERTIFICATE', 'Certificate'),
        ('OTHER', 'Other'),
    ])
    title = models.CharField(max_length=200)
    file_path = models.CharField(max_length=500)  # Store file path or URL
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.title}"

class EmployeeNote(models.Model):
    """Notes and comments about employees"""
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    note_type = models.CharField(max_length=20, choices=[
        ('GENERAL', 'General'),
        ('PERFORMANCE', 'Performance'),
        ('DISCIPLINARY', 'Disciplinary'),
        ('ACHIEVEMENT', 'Achievement'),
        ('TRAINING', 'Training'),
    ], default='GENERAL')
    is_confidential = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.get_note_type_display()} Note"
