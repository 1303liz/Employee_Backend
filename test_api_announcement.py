#!/usr/bin/env python
"""Test the announcements API endpoint"""
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_system.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import force_authenticate
from messaging.views import AnnouncementViewSet

User = get_user_model()

# Get an HR user
hr_user = User.objects.filter(role='HR').first()
if not hr_user:
    print("✗ No HR user found")
    exit(1)

print(f"Testing with user: {hr_user.username} (role: {hr_user.role})")
print(f"User role attribute exists: {hasattr(hr_user, 'role')}")
print(f"User role value: {getattr(hr_user, 'role', 'NO_ROLE')}")

# Create a mock request
factory = RequestFactory()
request = factory.post(
    '/api/messaging/announcements/',
    data=json.dumps({
        'title': 'Test API Announcement',
        'content': 'This is testing the API',
        'priority': 'normal'
    }),
    content_type='application/json'
)

# Authenticate the request
force_authenticate(request, user=hr_user)

# Create viewset and try to create announcement
viewset = AnnouncementViewSet.as_view({'post': 'create'})

try:
    response = viewset(request)
    print(f"\n✓ API request successful!")
    print(f"Status code: {response.status_code}")
    print(f"Response data: {response.data}")
    
    # Clean up
    if 'id' in response.data:
        from messaging.models import Announcement
        Announcement.objects.filter(id=response.data['id']).delete()
        print("\n✓ Test announcement deleted")
except Exception as e:
    print(f"\n✗ API request failed: {e}")
    import traceback
    traceback.print_exc()
