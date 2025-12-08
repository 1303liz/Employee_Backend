import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_system.settings')
django.setup()

from messaging.models import Message
from accounts.models import CustomUser

print("\n=== Database Check ===")
print(f"Total users: {CustomUser.objects.count()}")
print(f"Total messages: {Message.objects.count()}")

print("\n=== All Users ===")
for user in CustomUser.objects.all():
    print(f"  - {user.username} ({user.email}) - Role: {user.role}")

print("\n=== All Messages ===")
if Message.objects.count() == 0:
    print("  No messages found!")
    
    # Create test messages if there are at least 2 users
    if CustomUser.objects.count() >= 2:
        users = list(CustomUser.objects.all()[:2])
        user1, user2 = users[0], users[1]
        
        print(f"\n=== Creating Test Messages ===")
        # Message 1: user1 -> user2
        msg1 = Message.objects.create(
            sender=user1,
            recipient=user2,
            subject="Test Message 1",
            body="This is a test message from {} to {}".format(user1.username, user2.username)
        )
        print(f"  Created: {msg1}")
        
        # Message 2: user2 -> user1
        msg2 = Message.objects.create(
            sender=user2,
            recipient=user1,
            subject="Test Message 2",
            body="This is a test message from {} to {}".format(user2.username, user1.username)
        )
        print(f"  Created: {msg2}")
        
        # Message 3: user1 -> user2
        msg3 = Message.objects.create(
            sender=user1,
            recipient=user2,
            subject="Follow-up Message",
            body="This is a follow-up message"
        )
        print(f"  Created: {msg3}")
        
        print(f"\n✅ Created 3 test messages!")
else:
    for msg in Message.objects.all():
        print(f"  - Message #{msg.id}: {msg.sender.username} -> {msg.recipient.username}")
        print(f"    Subject: {msg.subject}")
        print(f"    Read: {msg.is_read}")
        print()
