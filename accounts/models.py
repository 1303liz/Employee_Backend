from django.contrib.auth.models import AbstractUser
from django.db import models
import os

def user_profile_photo_path(instance, filename):
    """Generate file path for user profile photo"""
    ext = filename.split('.')[-1]
    filename = f'profile_{instance.username}.{ext}'
    return os.path.join('profile_photos', filename)

def user_document_path(instance, filename):
    """Generate file path for user documents"""
    return os.path.join('user_documents', str(instance.user.username), filename)

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('EMPLOYEE', 'Employee'),
        ('HR', 'HR'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='EMPLOYEE')
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    must_change_password = models.BooleanField(default=False)
    
    # Profile information
    profile_photo = models.ImageField(upload_to=user_profile_photo_path, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=50, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_hr(self):
        return self.role == 'HR'
    
    @property
    def is_employee(self):
        return self.role == 'EMPLOYEE'

class UserDocument(models.Model):
    """Model for storing user documents like ID, certificates, etc."""
    DOCUMENT_TYPE_CHOICES = [
        ('ID', 'Identification Document'),
        ('RESUME', 'Resume/CV'),
        ('CERTIFICATE', 'Certificate'),
        ('CONTRACT', 'Employment Contract'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    document_name = models.CharField(max_length=200)
    document_file = models.FileField(upload_to=user_document_path)
    description = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.document_name}"

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
