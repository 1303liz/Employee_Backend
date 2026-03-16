from django.conf import settings
from django.core.mail import send_mail


def send_leave_status_email(leave_application):
    """Send leave approval/rejection status email to employee."""
    employee = getattr(leave_application, 'employee', None)
    if not employee or not employee.email:
        return {
            'success': False,
            'message': 'Employee email is not available.'
        }

    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    leave_url = f"{frontend_url}/leaves"

    employee_name = employee.get_full_name() or employee.username
    leave_type_name = leave_application.leave_type.name if leave_application.leave_type else 'Leave'

    is_approved = leave_application.status == 'APPROVED'
    subject = (
        f"Leave Request Approved - {leave_type_name}"
        if is_approved
        else f"Leave Request Rejected - {leave_type_name}"
    )

    decision_line = 'approved' if is_approved else 'rejected'
    comments = (leave_application.approval_comments or '').strip()

    message = f"""
Dear {employee_name},

Your leave request has been {decision_line}.

Leave Type: {leave_type_name}
Start Date: {leave_application.start_date}
End Date: {leave_application.end_date}
Total Days: {leave_application.total_days}
Status: {leave_application.get_status_display()}
"""

    if comments:
        message += f"\nHR Comments/Reason:\n{comments}\n"

    message += f"""

View your leave records: {leave_url}

Best regards,
HR Department
    """

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[employee.email],
            fail_silently=False,
        )
        return {
            'success': True,
            'message': 'Leave status email sent successfully.'
        }
    except Exception as exc:
        return {
            'success': False,
            'message': str(exc)
        }
