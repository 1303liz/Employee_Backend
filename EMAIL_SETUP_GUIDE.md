# Email Configuration Guide

## Overview
The Employee Management System can automatically send temporary passwords to newly created employees via email.

## Current Setup (Development)

By default, the system uses Django's **console backend**, which prints emails to the terminal instead of sending them. This is perfect for development and testing.

When you create a new employee, you'll see the email content in your backend terminal window.

## Email Flow

1. HR creates a new employee account
2. System generates a temporary password
3. System sends email to employee's email address
4. Employee receives:
   - Username
   - Temporary password
   - Instructions to change password after first login
5. HR sees confirmation that email was sent (or notification if it failed)

## Setting Up Real Email (Production)

### Option 1: Gmail SMTP (Recommended for small teams)

1. **Enable 2-Factor Authentication** on your Gmail account
   - Go to: https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Create a new app password for "Mail"
   - Copy the 16-character password

3. **Update `.env` file**:
   ```env
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-company-email@gmail.com
   EMAIL_HOST_PASSWORD=your-16-char-app-password
   DEFAULT_FROM_EMAIL=your-company-email@gmail.com
   ```

4. **Restart Django server**

### Option 2: Other Email Providers

#### Microsoft Outlook/Office 365
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=your-email@outlook.com
```

#### SendGrid (For production/bulk emails)
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@yourcompany.com
```

## Testing Email Configuration

After setting up email, test it by:

1. Creating a new employee with a valid email address
2. Check if the employee receives the email
3. Verify the email contains:
   - Welcome message
   - Username
   - Temporary password
   - Instructions for password change

## Troubleshooting

### Email not sending
1. Check terminal for error messages
2. Verify email credentials in `.env`
3. For Gmail: Ensure app password (not regular password) is used
4. Check firewall/antivirus settings
5. Verify EMAIL_BACKEND is set correctly

### Email goes to spam
1. Add sender to employee's contacts
2. Consider using a business email domain
3. Use services like SendGrid for better deliverability

### Console backend not showing emails
1. Ensure `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`
2. Check the terminal where `python manage.py runserver` is running
3. Look for email content between separator lines

## Security Best Practices

1. **Never commit** `.env` file to version control
2. Use **app passwords**, not regular passwords
3. Rotate email credentials periodically
4. Use environment-specific email accounts:
   - Development: test@company.com
   - Production: noreply@company.com
5. Monitor email sending logs
6. Implement rate limiting for email sending

## Email Template Customization

The email template is in `employees/email_utils.py`. You can customize:
- Subject line
- Message content
- Formatting
- Company branding

Example customization:
```python
subject = 'Welcome to [Your Company Name] - Account Setup'

message = f"""
Dear {employee_name},

Welcome to [Your Company Name]!

[Your custom message...]
"""
```

## Current Features

✅ Automatic email on employee creation
✅ Temporary password included
✅ Instructions for password change
✅ HR notification of email status
✅ Fallback message if email fails
✅ Console backend for development
✅ SMTP backend for production

## Future Enhancements

- HTML email templates with company logo
- Password reset via email
- Leave request notifications
- Attendance reminder emails
- Custom email templates for different events
