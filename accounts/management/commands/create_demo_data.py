from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Department
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo users and departments for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing demo data before creating new',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Deleting existing demo data...')
            User.objects.filter(username__in=['admin', 'hr_manager', 'employee1', 'employee2']).delete()
            Department.objects.filter(name__in=['Human Resources', 'Engineering', 'Sales', 'Marketing']).delete()

        # Create departments
        departments = [
            {'name': 'Human Resources', 'description': 'Manages employee relations and company policies'},
            {'name': 'Engineering', 'description': 'Software development and technical operations'},
            {'name': 'Sales', 'description': 'Customer acquisition and revenue generation'},
            {'name': 'Marketing', 'description': 'Brand promotion and market research'},
        ]

        for dept_data in departments:
            dept, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={'description': dept_data['description']}
            )
            if created:
                self.stdout.write(f'Created department: {dept.name}')
            else:
                self.stdout.write(f'Department already exists: {dept.name}')

        # Create superuser
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@company.com',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                role='HR'
            )
            self.stdout.write(self.style.SUCCESS('Created superuser: admin/admin123'))
        else:
            self.stdout.write('Superuser already exists: admin')

        # Create HR user
        if not User.objects.filter(username='hr_manager').exists():
            hr_user = User.objects.create_user(
                username='hr_manager',
                email='hr@company.com',
                password='hr123456',
                first_name='Jane',
                last_name='Smith',
                role='HR',
                employee_id='HR001',
                department='Human Resources',
                phone_number='+1-555-0101',
                hire_date=date(2023, 1, 15)
            )
            self.stdout.write(self.style.SUCCESS('Created HR user: hr_manager/hr123456'))
        else:
            self.stdout.write('HR user already exists: hr_manager')

        # Create employee users
        employees = [
            {
                'username': 'employee1',
                'email': 'john.doe@company.com',
                'password': 'emp123456',
                'first_name': 'John',
                'last_name': 'Doe',
                'employee_id': 'EMP001',
                'department': 'Engineering',
                'phone_number': '+1-555-0102',
                'hire_date': date(2023, 3, 1)
            },
            {
                'username': 'employee2',
                'email': 'alice.johnson@company.com',
                'password': 'emp123456',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'employee_id': 'EMP002',
                'department': 'Sales',
                'phone_number': '+1-555-0103',
                'hire_date': date(2023, 2, 15)
            },
        ]

        for emp_data in employees:
            if not User.objects.filter(username=emp_data['username']).exists():
                employee = User.objects.create_user(
                    username=emp_data['username'],
                    email=emp_data['email'],
                    password=emp_data['password'],
                    first_name=emp_data['first_name'],
                    last_name=emp_data['last_name'],
                    role='EMPLOYEE',
                    employee_id=emp_data['employee_id'],
                    department=emp_data['department'],
                    phone_number=emp_data['phone_number'],
                    hire_date=emp_data['hire_date']
                )
                self.stdout.write(self.style.SUCCESS(f'Created employee: {emp_data["username"]}/emp123456'))
            else:
                self.stdout.write(f'Employee already exists: {emp_data["username"]}')

        self.stdout.write(self.style.SUCCESS('\nDemo data creation complete!'))
        self.stdout.write('\nDemo login credentials:')
        self.stdout.write('Admin: admin/admin123 (Superuser)')
        self.stdout.write('HR Manager: hr_manager/hr123456 (HR Role)')
        self.stdout.write('Employee 1: employee1/emp123456 (Employee Role)')
        self.stdout.write('Employee 2: employee2/emp123456 (Employee Role)')