import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_system.settings')
django.setup()

from messaging.models import Message
from accounts.models import CustomUser
from django.contrib.auth import get_user_model

print("\n=== Testing Message Retrieval ===")

# Get users
users = list(CustomUser.objects.all())
if len(users) < 2:
    print("❌ Not enough users in database!")
    exit(1)

user1 = users[0]  # liza (HR)
user2 = users[1]  # suxxy (EMPLOYEE)

print(f"\n📋 User 1: {user1.username} ({user1.role})")
print(f"📋 User 2: {user2.username} ({user2.role})")

# Check all messages
all_messages = Message.objects.all()
print(f"\n📧 Total messages in database: {all_messages.count()}")

# Check messages for user1 (liza - HR)
print(f"\n--- Messages for {user1.username} (HR) ---")
user1_received = Message.objects.filter(recipient=user1, parent_message__isnull=True)
user1_sent = Message.objects.filter(sender=user1, parent_message__isnull=True)
print(f"  Received: {user1_received.count()}")
for msg in user1_received:
    print(f"    • From {msg.sender.username}: {msg.subject} (Read: {msg.is_read})")
print(f"  Sent: {user1_sent.count()}")
for msg in user1_sent:
    print(f"    • To {msg.recipient.username}: {msg.subject}")

# Check messages for user2 (suxxy - EMPLOYEE)
print(f"\n--- Messages for {user2.username} (EMPLOYEE) ---")
user2_received = Message.objects.filter(recipient=user2, parent_message__isnull=True)
user2_sent = Message.objects.filter(sender=user2, parent_message__isnull=True)
print(f"  Received: {user2_received.count()}")
for msg in user2_received:
    print(f"    • From {msg.sender.username}: {msg.subject} (Read: {msg.is_read})")
print(f"  Sent: {user2_sent.count()}")
for msg in user2_sent:
    print(f"    • To {msg.recipient.username}: {msg.subject}")

# Test the queryset that the view uses
print("\n--- Testing ViewSet Queryset ---")
from django.db.models import Q

def get_queryset_for_user(user):
    return Message.objects.filter(
        Q(sender=user) | Q(recipient=user)
    ).select_related('sender', 'recipient', 'parent_message')

print(f"\n{user1.username}'s queryset: {get_queryset_for_user(user1).count()} messages")
for msg in get_queryset_for_user(user1):
    direction = "Sent to" if msg.sender == user1 else "Received from"
    other_user = msg.recipient.username if msg.sender == user1 else msg.sender.username
    print(f"  • {direction} {other_user}: {msg.subject}")

print(f"\n{user2.username}'s queryset: {get_queryset_for_user(user2).count()} messages")
for msg in get_queryset_for_user(user2):
    direction = "Sent to" if msg.sender == user2 else "Received from"
    other_user = msg.recipient.username if msg.sender == user2 else msg.sender.username
    print(f"  • {direction} {other_user}: {msg.subject}")

print("\n✅ Database query test complete!")
