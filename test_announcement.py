#!/usr/bin/env python
"""Test script to check announcement creation"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_system.settings')
django.setup()

from accounts.models import CustomUser
from messaging.models import Announcement

# Get an HR user
try:
    hr_user = CustomUser.objects.filter(role='HR').first()
    if hr_user:
        print(f"Found HR user: {hr_user.username} (role: {hr_user.role})")
        
        # Try to create an announcement
        announcement = Announcement.objects.create(
            sender=hr_user,
            title="Test Announcement",
            content="This is a test announcement",
            priority="normal"
        )
        print(f"✓ Successfully created announcement: {announcement.id}")
        
        # Clean up
        announcement.delete()
        print("✓ Test announcement deleted")
    else:
        print("✗ No HR users found in database")
        print("Available users:")
        for user in CustomUser.objects.all()[:5]:
            print(f"  - {user.username}: role={user.role}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
