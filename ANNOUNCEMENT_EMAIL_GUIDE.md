# Announcement Email Notifications

## Overview

The Employee Management System now automatically sends email notifications to all employees whenever a new announcement is created by HR. This ensures that important company-wide communications reach all staff members directly in their email inbox.

## Features

✅ **Automatic Email Delivery**: When HR creates a new announcement, emails are automatically sent to all active employees

✅ **Priority-Based Formatting**: Emails are formatted based on announcement priority (Urgent, High, Normal, Low) with appropriate emojis and labels

✅ **Professional Design**: Clean, well-formatted emails with clear sections and information hierarchy

✅ **Smart Recipient Filtering**: 
- Excludes the announcement sender
- Only sends to active employees
- Only sends to employees with valid email addresses

✅ **Direct Link**: Includes a link to view the announcement in the system

✅ **Failure Tolerance**: Email failures don't prevent announcement creation

## How It Works

### 1. HR Creates an Announcement

When an HR user creates an announcement through the API or frontend:

```
POST /api/messaging/announcements/
{
  "title": "Important Company Update",
  "content": "All employees please note...",
  "priority": "high"
}
```

### 2. Automatic Email Sending

The system automatically:
1. Saves the announcement to the database
2. Retrieves all active employees (excluding the sender)
3. Generates personalized emails for each employee
4. Sends all emails in batch using Django's mass email functionality
5. Logs the result (number of emails sent)

### 3. Email Format

Employees receive emails with:
- **Subject**: Priority emoji + "New Announcement: {title}"
- **Priority Label**: Clear visual indicator (URGENT, HIGH PRIORITY, NOTICE, INFO)
- **Announcement Details**: Title, posted by, date/time
- **Full Content**: Complete announcement message
- **Action Link**: Direct link to view in the system

### Example Email

```
Subject: 🚨 New Announcement: Important Company Update

Dear John Smith,

🚨 A new announcement has been posted!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Priority: URGENT
Title: Important Company Update
Posted by: Jane Doe (HR Manager)
Date: February 13, 2026 at 02:30 PM

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MESSAGE:
All employees please note that we will have a mandatory meeting...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 VIEW ANNOUNCEMENTS:
Click here to view all announcements: http://localhost:5173/messaging/announcements

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated notification from the Employee Management System.
Please do not reply to this email.

Best regards,
HR Department
```

## Priority Levels

| Priority | Emoji | Label | Use Case |
|----------|-------|-------|----------|
| Urgent | 🚨 | URGENT | Critical announcements requiring immediate attention |
| High | 📢 | HIGH PRIORITY | Important announcements that need prompt attention |
| Normal | ℹ️ | NOTICE | Standard company communications |
| Low | 📌 | INFO | General information or updates |

## Configuration

### Email Settings Required

Make sure your `.env` file has these settings configured:

```env
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Frontend URL (for links in emails)
FRONTEND_URL=http://localhost:5173
```

### Gmail Setup

For Gmail accounts, you need to:
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password in `EMAIL_HOST_PASSWORD`

See `EMAIL_SETUP_GUIDE.md` for detailed instructions.

## Testing

### Test Email Notifications

Run the test script to verify email functionality:

```bash
python test_announcement_email.py
```

This script will:
1. Check your email configuration
2. Verify HR users exist
3. List employees who will receive emails
4. Create a test announcement
5. Send test emails
6. Show results and allow cleanup

### Manual Testing

1. Log in as an HR user
2. Navigate to Messaging > Announcements
3. Create a new announcement
4. Check employee email inboxes for the notification

## Troubleshooting

### Emails Not Being Sent

**Problem**: Announcements are created but no emails are sent

**Solutions**:
1. Check email configuration in `.env`
2. Verify `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are set
3. For Gmail, ensure you're using an App Password
4. Check Django logs for email errors

### Some Employees Not Receiving Emails

**Problem**: Only some employees receive emails

**Possible Causes**:
- Employees without email addresses (check user profiles)
- Inactive employee accounts
- Email addresses are invalid

**Check**:
```python
# Run in Django shell
python manage.py shell
>>> from accounts.models import CustomUser
>>> employees = CustomUser.objects.filter(is_active=True)
>>> for emp in employees:
...     print(f"{emp.username}: {emp.email or 'NO EMAIL'}")
```

### Email Delivery Delays

**Note**: Email delivery depends on:
- Your SMTP server speed
- Number of recipients
- Internet connection
- Email provider's rate limits

For Gmail, there may be sending limits (usually 500-2000/day for regular accounts).

## Technical Implementation

### Files Modified

1. **messaging/views.py**
   - Modified `AnnouncementViewSet.perform_create()` to call email notification function

### Files Used

1. **messaging/email_utils.py**
   - Contains `send_announcement_notification()` function
   - Handles email generation and sending

2. **messaging/models.py**
   - `Announcement` model with priority levels

## API Response

When creating an announcement, the response remains the same:

```json
{
  "id": 1,
  "title": "Important Update",
  "content": "Message content...",
  "priority": "high",
  "sender": {
    "id": 2,
    "username": "hruser",
    "first_name": "Jane",
    "last_name": "Doe"
  },
  "created_at": "2026-02-13T14:30:00Z",
  "is_active": true
}
```

Email sending happens in the background and doesn't affect the API response. If email sending fails, the announcement is still created successfully.

## Future Enhancements

Potential improvements:
- [ ] Add email preferences (allow users to opt-out of announcement emails)
- [ ] Support HTML email templates
- [ ] Add read receipts/tracking
- [ ] Schedule announcements for future delivery
- [ ] Send digest emails (daily/weekly summaries)
- [ ] Add email attachments support
- [ ] SMS notifications for urgent announcements

## Support

For issues or questions:
1. Check `EMAIL_SETUP_GUIDE.md` for email configuration
2. Run `python test_announcement_email.py` to diagnose issues
3. Check Django logs for error messages
4. Verify employee email addresses are correct in the system
