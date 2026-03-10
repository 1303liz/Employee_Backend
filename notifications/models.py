from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Notification(models.Model):
    """Model for system notifications"""
    
    NOTIFICATION_TYPES = [
        ('MESSAGE', 'New Message'),
        ('ANNOUNCEMENT', 'New Announcement'), 
        ('LEAVE_ENDING', 'Leave Ending Soon'),
        ('LEAVE_APPROVED', 'Leave Approved'),
        ('LEAVE_REJECTED', 'Leave Rejected'),
        ('LEAVE_PENDING', 'Leave Pending Review'),
        ('TASK_ASSIGNED', 'Task Assigned'),
        ('TASK_DUE', 'Task Due Soon'),
        ('TASK_OVERDUE', 'Task Overdue'),
        ('ATTENDANCE_REMINDER', 'Attendance Reminder'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')
    
    # Related objects (optional)
    related_message_id = models.IntegerField(null=True, blank=True)
    related_leave_id = models.IntegerField(null=True, blank=True)
    related_task_id = models.IntegerField(null=True, blank=True)
    
    # Status fields
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.title} for {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def dismiss(self):
        """Dismiss notification"""
        self.is_dismissed = True
        self.save(update_fields=['is_dismissed'])
    
    @classmethod
    def create_message_notification(cls, message):
        """Create notification for new message"""
        return cls.objects.create(
            recipient=message.recipient,
            notification_type='MESSAGE',
            title=f"New message from {message.sender.get_full_name() or message.sender.username}",
            message=f"Subject: {message.subject}",
            related_message_id=message.id,
            priority='MEDIUM'
        )
    
    @classmethod
    def create_announcement_notification(cls, announcement, users):
        """Create notifications for new announcement"""
        notifications = []
        for user in users:
            notifications.append(cls(
                recipient=user,
                notification_type='ANNOUNCEMENT',
                title=f"New Announcement: {announcement.title}",
                message=announcement.content[:100] + ('...' if len(announcement.content) > 100 else ''),
                priority=announcement.priority.upper() if announcement.priority else 'MEDIUM'
            ))
        return cls.objects.bulk_create(notifications)
    
    @classmethod
    def create_leave_ending_notification(cls, leave_application):
        """Create notification for leave ending soon"""
        days_until_end = (leave_application.end_date - timezone.now().date()).days
        return cls.objects.create(
            recipient=leave_application.employee,
            notification_type='LEAVE_ENDING',
            title="Your leave is ending soon",
            message=f"Your {leave_application.leave_type.name} leave ends in {days_until_end} day{'s' if days_until_end != 1 else ''}",
            related_leave_id=leave_application.id,
            priority='HIGH' if days_until_end <= 1 else 'MEDIUM'
        )
    
    @classmethod
    def create_leave_status_notification(cls, leave_application, status):
        """Create notification for leave status change"""
        status_map = {
            'APPROVED': ('LEAVE_APPROVED', 'Your leave has been approved'),
            'REJECTED': ('LEAVE_REJECTED', 'Your leave has been rejected'),
            'PENDING': ('LEAVE_PENDING', 'Your leave is pending review')
        }
        
        if status in status_map:
            notification_type, message = status_map[status]
            return cls.objects.create(
                recipient=leave_application.employee,
                notification_type=notification_type,
                title=f"Leave Application {status.title()}",
                message=f"{message}: {leave_application.leave_type.name} ({leave_application.start_date} to {leave_application.end_date})",
                related_leave_id=leave_application.id,
                priority='HIGH' if status == 'APPROVED' or status == 'REJECTED' else 'MEDIUM'
            )


class Task(models.Model):
    """Model for employee tasks"""
    
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_tasks'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tasks'
    )
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='TODO')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.assigned_to.username}"
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        return self.due_date < timezone.now() and self.status not in ['COMPLETED', 'CANCELLED']
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        delta = self.due_date.date() - timezone.now().date()
        return delta.days
    
    def mark_completed(self):
        """Mark task as completed"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])


class NotificationPreference(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email notification preferences
    email_messages = models.BooleanField(default=True)
    email_announcements = models.BooleanField(default=True)
    email_leave_updates = models.BooleanField(default=True)
    email_task_assignments = models.BooleanField(default=True)
    
    # In-app notification preferences
    app_messages = models.BooleanField(default=True)
    app_announcements = models.BooleanField(default=True)
    app_leave_updates = models.BooleanField(default=True)
    app_task_assignments = models.BooleanField(default=True)
    
    # Frequency settings
    digest_frequency = models.CharField(
        max_length=10,
        choices=[
            ('NONE', 'None'),
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
        ],
        default='DAILY'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"