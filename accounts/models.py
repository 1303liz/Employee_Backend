from django.contrib.auth.models import AbstractUser
from django.db import models

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
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_hr(self):
        return self.role == 'HR'
    
    @property
    def is_employee(self):
        return self.role == 'EMPLOYEE'

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
