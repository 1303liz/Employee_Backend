from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ai_services.ai_engine import AIServiceManager
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run daily AI analysis for all employees'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--employee-id',
            type=int,
            help='Run analysis for specific employee ID only'
        )
        parser.add_argument(
            '--services',
            nargs='+',
            choices=['attendance', 'mood', 'leave'],
            default=['attendance', 'mood', 'leave'],
            help='Specify which AI services to run'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force analysis even if already done today'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting daily AI analysis...')
        )
        
        try:
            employee_id = options.get('employee_id')
            services = options.get('services')
            force = options.get('force', False)
            
            # Initialize AI manager
            manager = AIServiceManager()
            
            # Determine which employees to analyze
            if employee_id:
                try:
                    employee = User.objects.get(id=employee_id)
                    employees = [employee]
                    self.stdout.write(
                        f'Running analysis for employee: {employee.username}'
                    )
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Employee with ID {employee_id} not found')
                    )
                    return
            else:
                employees = User.objects.filter(employeeprofile__isnull=False)
                self.stdout.write(
                    f'Running analysis for {employees.count()} employees'
                )
            
            # Run analysis for each employee
            total_processed = 0
            total_errors = 0
            
            for employee in employees:
                try:
                    self.stdout.write(f'Processing {employee.username}...')
                    
                    # Run specific services
                    if 'attendance' in services:
                        attendance_result = manager.attendance_service.predict_attendance(employee)
                        self.stdout.write(f'  ✓ Attendance prediction: {attendance_result.get("absence_risk", "N/A")} risk')
                    
                    if 'mood' in services:
                        mood_result = manager.mood_service.analyze_employee_mood(employee)
                        self.stdout.write(f'  ✓ Mood analysis: {mood_result.get("mood_category", "N/A")}')
                    
                    if 'leave' in services:
                        leave_result = manager.leave_service.generate_leave_recommendation(employee)
                        rec_count = leave_result.get("total_recommendations", 0)
                        self.stdout.write(f'  ✓ Leave recommendations: {rec_count} generated')
                    
                    total_processed += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error processing {employee.username}: {str(e)}')
                    )
                    total_errors += 1
                    logger.error(f'AI analysis error for {employee.username}: {str(e)}')
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'\\nDaily AI analysis completed!'
                    f'\\n  Processed: {total_processed} employees'
                    f'\\n  Errors: {total_errors} employees'
                    f'\\n  Services run: {", ".join(services)}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Fatal error running daily AI analysis: {str(e)}')
            )
            logger.error(f'Fatal AI analysis error: {str(e)}')