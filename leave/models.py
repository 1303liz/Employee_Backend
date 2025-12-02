from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from datetime import date, timedelta

User = get_user_model()

class LeaveType(models.Model):
    """Different types of leave available"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    max_days_per_year = models.PositiveIntegerField(
        default=30,
        help_text="Maximum days allowed per year for this leave type"
    )
    requires_approval = models.BooleanField(
        default=True,
        help_text="Whether this leave type requires HR approval"
    )
    advance_notice_days = models.PositiveIntegerField(
        default=7,
        help_text="Minimum days of advance notice required"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class LeaveBalance(models.Model):
    """Employee's leave balance for different leave types"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(default=date.today().year)
    
    total_allocated = models.DecimalField(
        max_digits=5, decimal_places=1, default=0,
        help_text="Total days allocated for this year"
    )
    used_days = models.DecimalField(
        max_digits=5, decimal_places=1, default=0,
        help_text="Days already used/approved"
    )
    pending_days = models.DecimalField(
        max_digits=5, decimal_places=1, default=0,
        help_text="Days in pending applications"
    )
    
    class Meta:
        unique_together = ['user', 'leave_type', 'year']
        ordering = ['user', 'leave_type', 'year']
    
    def __str__(self):
        return f"{self.user.username} - {self.leave_type.name} ({self.year})"
    
    @property
    def available_days(self):
        """Calculate remaining available days"""
        return self.total_allocated - self.used_days - self.pending_days
    
    @property
    def utilization_percentage(self):
        """Calculate percentage of leave used"""
        if self.total_allocated > 0:
            return (self.used_days / self.total_allocated) * 100
        return 0

class LeaveApplication(models.Model):
    """Leave application requests"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    # Basic Information
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    
    # Leave Details
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.DecimalField(max_digits=4, decimal_places=1)
    reason = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Contact Information
    contact_number = models.CharField(max_length=15, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    
    # Application Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    applied_on = models.DateTimeField(auto_now_add=True)
    
    # Approval Information
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_leaves', limit_choices_to={'role': 'HR'}
    )
    approved_on = models.DateTimeField(null=True, blank=True)
    approval_comments = models.TextField(blank=True)
    
    # Additional Information
    is_half_day = models.BooleanField(default=False)
    replacement_employee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='covering_leaves'
    )
    
    class Meta:
        ordering = ['-applied_on']
    
    def __str__(self):
        return f"{self.employee.get_full_name() or self.employee.username} - {self.leave_type.name} ({self.start_date} to {self.end_date})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate dates
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError('End date cannot be before start date.')
            
            if self.start_date < date.today():
                raise ValidationError('Cannot apply for leave in the past.')
            
            # Check advance notice
            if self.leave_type and self.leave_type.advance_notice_days:
                required_date = date.today() + timedelta(days=self.leave_type.advance_notice_days)
                if self.start_date < required_date:
                    raise ValidationError(
                        f'This leave type requires {self.leave_type.advance_notice_days} days advance notice.'
                    )
    
    def calculate_days(self):
        """Calculate total days including weekends/holidays logic"""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            days = delta.days + 1  # Include both start and end date
            
            if self.is_half_day:
                days = days * 0.5
                
            return days
        return 0
    
    def save(self, *args, **kwargs):
        # Auto-calculate total days
        if not self.total_days:
            self.total_days = self.calculate_days()
        
        super().save(*args, **kwargs)
        
        # Update leave balance if approved
        if self.status == 'APPROVED' and self.employee:
            self.update_leave_balance()
    
    def update_leave_balance(self):
        """Update employee's leave balance when leave is approved"""
        balance, created = LeaveBalance.objects.get_or_create(
            user=self.employee,
            leave_type=self.leave_type,
            year=self.start_date.year,
            defaults={
                'total_allocated': self.leave_type.max_days_per_year
            }
        )
        
        if created:
            balance.total_allocated = self.leave_type.max_days_per_year
        
        # Move from pending to used
        if hasattr(self, '_previous_status') and self._previous_status == 'PENDING':
            balance.pending_days = max(0, balance.pending_days - self.total_days)
        
        balance.used_days += self.total_days
        balance.save()

class LeaveApplicationAttachment(models.Model):
    """Attachments for leave applications (medical certificates, etc.)"""
    leave_application = models.ForeignKey(
        LeaveApplication, on_delete=models.CASCADE, 
        related_name='attachments'
    )
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.leave_application} - {self.file_name}"

class LeaveApplicationComment(models.Model):
    """Comments on leave applications"""
    leave_application = models.ForeignKey(
        LeaveApplication, on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text="Internal comments visible only to HR"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.leave_application} - Comment by {self.author.username}"
