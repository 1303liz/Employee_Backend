from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_temporary_password_email(employee_email, employee_name, username, temporary_password, login_url=None):
    """
    Send temporary password email to newly created employee
    
    Args:
        employee_email: Email address of the employee
        employee_name: Full name of the employee
        username: Username for login
        temporary_password: Temporary password generated
        login_url: Optional login URL (defaults to frontend URL from settings)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    # Get login URL from settings or use default
    if not login_url:
        frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:5173'
        login_url = f"{frontend_url}/login"
    
    subject = 'Welcome to Employee Management System - Your Account Details'
    
    message = f"""
Dear {employee_name},

Welcome to the Employee Management System!

Your account has been created successfully. Below are your login credentials:

Username: {username}
Temporary Password: {temporary_password}

For security reasons, you will be required to change your password after your first login.

🔗 ACCESS YOUR ACCOUNT:
Click here to login: {login_url}

Or copy and paste this link in your browser:
{login_url}

Login Instructions:
1. Click the link above or go to the login page
2. Enter your username and temporary password
3. You will be automatically redirected to change your password
4. After changing your password, you can access your dashboard

If you have any questions or need assistance, please contact the HR department.

Best regards,
HR Department
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[employee_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email to {employee_email}: {str(e)}")
        return False
