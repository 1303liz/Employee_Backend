from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.template.loader import render_to_string
from accounts.models import CustomUser


def send_announcement_notification(announcement):
    """
    Send email notification to all employees when a new announcement is created
    
    Args:
        announcement: Announcement model instance
    
    Returns:
        dict with success status and count of emails sent
    """
    # Get all active employees (exclude the sender)
    employees = CustomUser.objects.filter(
        is_active=True
    ).exclude(id=announcement.sender.id)
    
    if not employees.exists():
        return {
            'success': True,
            'sent_count': 0,
            'message': 'No employees to notify'
        }
    
    # Get frontend URL for announcement link
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    announcement_url = f"{frontend_url}/messaging/announcements"
    
    # Determine priority emoji and styling
    priority_info = {
        'urgent': {'emoji': '🚨', 'label': 'URGENT', 'color': '#FF6B6B'},
        'high': {'emoji': '📢', 'label': 'HIGH PRIORITY', 'color': '#FFA94D'},
        'normal': {'emoji': 'ℹ️', 'label': 'NOTICE', 'color': '#4DABF7'},
        'low': {'emoji': '📌', 'label': 'INFO', 'color': '#A3BE8C'}
    }
    
    priority = priority_info.get(announcement.priority.lower(), priority_info['normal'])
    
    subject = f"{priority['emoji']} New Announcement: {announcement.title}"
    
    # Create list of email tuples for mass email
    email_messages = []
    
    for employee in employees:
        if not employee.email:
            continue
            
        message = f"""
Dear {employee.first_name or employee.username},

{priority['emoji']} A new announcement has been posted!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Priority: {priority['label']}
Title: {announcement.title}
Posted by: {announcement.sender.get_full_name() or announcement.sender.username}
Date: {announcement.created_at.strftime('%B %d, %Y at %I:%M %p')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MESSAGE:
{announcement.content}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 VIEW ANNOUNCEMENTS:
Click here to view all announcements: {announcement_url}

Or copy and paste this link in your browser:
{announcement_url}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated notification from the Employee Management System.
Please do not reply to this email.

Best regards,
HR Department
        """
        
        email_messages.append((
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [employee.email]
        ))
    
    # Send all emails
    try:
        sent_count = send_mass_mail(email_messages, fail_silently=False)
        return {
            'success': True,
            'sent_count': sent_count,
            'message': f'Successfully sent {sent_count} notification emails'
        }
    except Exception as e:
        print(f"Error sending announcement emails: {str(e)}")
        return {
            'success': False,
            'sent_count': 0,
            'message': f'Error sending emails: {str(e)}'
        }


def send_announcement_to_specific_employees(announcement, employee_ids):
    """
    Send announcement notification to specific employees
    
    Args:
        announcement: Announcement model instance
        employee_ids: List of employee IDs to notify
    
    Returns:
        dict with success status and count of emails sent
    """
    employees = CustomUser.objects.filter(
        id__in=employee_ids,
        is_active=True
    ).exclude(id=announcement.sender.id)
    
    if not employees.exists():
        return {
            'success': True,
            'sent_count': 0,
            'message': 'No employees to notify'
        }
    
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    announcement_url = f"{frontend_url}/messaging/announcements"
    
    priority_info = {
        'urgent': {'emoji': '🚨', 'label': 'URGENT', 'color': '#FF6B6B'},
        'high': {'emoji': '📢', 'label': 'HIGH PRIORITY', 'color': '#FFA94D'},
        'normal': {'emoji': 'ℹ️', 'label': 'NOTICE', 'color': '#4DABF7'},
        'low': {'emoji': '📌', 'label': 'INFO', 'color': '#A3BE8C'}
    }
    
    priority = priority_info.get(announcement.priority.lower(), priority_info['normal'])
    subject = f"{priority['emoji']} New Announcement: {announcement.title}"
    
    email_messages = []
    
    for employee in employees:
        if not employee.email:
            continue
            
        message = f"""
Dear {employee.first_name or employee.username},

{priority['emoji']} A new announcement has been posted!

Priority: {priority['label']}
Title: {announcement.title}
Posted by: {announcement.sender.get_full_name() or announcement.sender.username}

MESSAGE:
{announcement.content}

View announcements: {announcement_url}

Best regards,
HR Department
        """
        
        email_messages.append((
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [employee.email]
        ))
    
    try:
        sent_count = send_mass_mail(email_messages, fail_silently=False)
        return {
            'success': True,
            'sent_count': sent_count,
            'message': f'Successfully sent {sent_count} notification emails'
        }
    except Exception as e:
        print(f"Error sending announcement emails: {str(e)}")
        return {
            'success': False,
            'sent_count': 0,
            'message': f'Error sending emails: {str(e)}'
        }
