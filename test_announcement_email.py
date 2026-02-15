#!/usr/bin/env python
"""Test script to verify announcement email notifications"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_system.settings')
django.setup()

from accounts.models import CustomUser
from messaging.models import Announcement
from messaging.email_utils import send_announcement_notification
from django.conf import settings

def test_announcement_email():
    """Test the announcement email notification system"""
    
    print("=" * 70)
    print("ANNOUNCEMENT EMAIL NOTIFICATION TEST")
    print("=" * 70)
    
    # Check email configuration
    print("\n📧 EMAIL CONFIGURATION:")
    print(f"  Backend: {settings.EMAIL_BACKEND}")
    print(f"  Host: {settings.EMAIL_HOST}")
    print(f"  Port: {settings.EMAIL_PORT}")
    print(f"  Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"  From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"  Host User: {settings.EMAIL_HOST_USER or '(not configured)'}")
    
    if not settings.EMAIL_HOST_USER:
        print("\n⚠️  WARNING: EMAIL_HOST_USER is not configured!")
        print("  Please set up email credentials in your .env file")
        print("  See EMAIL_SETUP_GUIDE.md for instructions")
    
    # Get HR user
    print("\n👤 LOOKING FOR HR USER:")
    hr_user = CustomUser.objects.filter(role='HR').first()
    if not hr_user:
        print("  ✗ No HR users found in database")
        print("\n  Available users:")
        for user in CustomUser.objects.all()[:5]:
            print(f"    - {user.username} (role: {user.role})")
        return
    
    print(f"  ✓ Found HR user: {hr_user.username} ({hr_user.email})")
    
    # Check for employees
    print("\n👥 CHECKING EMPLOYEES:")
    employees = CustomUser.objects.filter(is_active=True).exclude(id=hr_user.id)
    employee_count = employees.count()
    
    if employee_count == 0:
        print("  ✗ No employees found to notify")
        return
    
    print(f"  ✓ Found {employee_count} active employee(s)")
    
    employees_with_email = employees.exclude(email='').exclude(email__isnull=True)
    email_count = employees_with_email.count()
    
    print(f"  ✓ {email_count} employee(s) with email addresses:")
    for emp in employees_with_email[:10]:  # Show first 10
        print(f"    - {emp.username}: {emp.email}")
    
    if email_count < employee_count:
        print(f"  ⚠️  {employee_count - email_count} employee(s) without email addresses")
    
    # Create test announcement
    print("\n📢 CREATING TEST ANNOUNCEMENT:")
    try:
        announcement = Announcement.objects.create(
            sender=hr_user,
            title="System Test - Email Notification",
            content="This is a test announcement to verify that email notifications are working correctly. If you receive this email, the system is functioning properly!",
            priority="high"
        )
        print(f"  ✓ Created announcement #{announcement.id}: {announcement.title}")
        print(f"    Priority: {announcement.priority}")
        print(f"    Created at: {announcement.created_at}")
    except Exception as e:
        print(f"  ✗ Failed to create announcement: {e}")
        return
    
    # Test email notification
    print("\n📨 SENDING EMAIL NOTIFICATIONS:")
    try:
        result = send_announcement_notification(announcement)
        
        if result['success']:
            print(f"  ✓ {result['message']}")
            print(f"  ✓ Emails sent: {result['sent_count']}")
        else:
            print(f"  ✗ Failed: {result.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"  ✗ Error sending emails: {e}")
        import traceback
        traceback.print_exc()
    
    # Ask if should keep or delete the test announcement
    print("\n🗑️  CLEANUP:")
    keep = input("  Keep test announcement? (y/n): ").lower()
    if keep != 'y':
        announcement.delete()
        print("  ✓ Test announcement deleted")
    else:
        print(f"  ✓ Test announcement kept (ID: {announcement.id})")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    test_announcement_email()
