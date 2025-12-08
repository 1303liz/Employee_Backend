from django.core.management.base import BaseCommand
from leave.models import LeaveType


class Command(BaseCommand):
    help = 'Creates default leave types'

    def handle(self, *args, **kwargs):
        leave_types = [
            {
                'name': 'Annual Leave',
                'description': 'Regular paid time off for vacation, personal matters, or rest.',
                'max_days_per_year': 20,
                'requires_approval': True,
                'advance_notice_days': 7
            },
            {
                'name': 'Sick Leave',
                'description': 'Time off for illness, injury, or medical appointments.',
                'max_days_per_year': 15,
                'requires_approval': True,
                'advance_notice_days': 1
            },
            {
                'name': 'Casual Leave',
                'description': 'Short-term leave for personal or urgent matters.',
                'max_days_per_year': 10,
                'requires_approval': True,
                'advance_notice_days': 2
            },
            {
                'name': 'Maternity Leave',
                'description': 'Leave for expecting mothers before and after childbirth.',
                'max_days_per_year': 90,
                'requires_approval': True,
                'advance_notice_days': 30
            },
            {
                'name': 'Paternity Leave',
                'description': 'Leave for fathers following the birth of a child.',
                'max_days_per_year': 14,
                'requires_approval': True,
                'advance_notice_days': 7
            },
            {
                'name': 'Bereavement Leave',
                'description': 'Leave following the death of a close family member.',
                'max_days_per_year': 5,
                'requires_approval': True,
                'advance_notice_days': 0
            },
            {
                'name': 'Unpaid Leave',
                'description': 'Leave without pay for extended personal reasons.',
                'max_days_per_year': 30,
                'requires_approval': True,
                'advance_notice_days': 14
            },
            {
                'name': 'Study Leave',
                'description': 'Leave for educational or professional development purposes.',
                'max_days_per_year': 10,
                'requires_approval': True,
                'advance_notice_days': 14
            },
        ]

        created_count = 0
        existing_count = 0

        for leave_data in leave_types:
            leave_type, created = LeaveType.objects.get_or_create(
                name=leave_data['name'],
                defaults={
                    'description': leave_data['description'],
                    'max_days_per_year': leave_data['max_days_per_year'],
                    'requires_approval': leave_data['requires_approval'],
                    'advance_notice_days': leave_data['advance_notice_days'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created leave type: {leave_type.name}')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'- Leave type already exists: {leave_type.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Summary: {created_count} created, {existing_count} already existed'
            )
        )
