# Generated manually for hr_management app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CandidateProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=254)),
                ('phone_number', models.CharField(blank=True, max_length=50)),
                ('position_applied', models.CharField(max_length=120)),
                ('resume_link', models.URLField(blank=True)),
                ('status', models.CharField(choices=[('NEW', 'New'), ('UNDER_REVIEW', 'Under Review'), ('SHORTLISTED', 'Shortlisted'), ('REJECTED', 'Rejected')], default='NEW', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='PerformanceReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_period', models.CharField(max_length=50)),
                ('overall_rating', models.DecimalField(decimal_places=1, max_digits=3)),
                ('strengths', models.TextField(blank=True)),
                ('improvement_areas', models.TextField(blank=True)),
                ('goals', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('FINALIZED', 'Finalized')], default='DRAFT', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='performance_reviews', to=settings.AUTH_USER_MODEL)),
                ('reviewer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviews_conducted', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='RecruitmentQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField()),
                ('category', models.CharField(choices=[('TECHNICAL', 'Technical'), ('BEHAVIORAL', 'Behavioral'), ('EXPERIENCE', 'Experience'), ('GENERAL', 'General')], default='GENERAL', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='TrainingProgram',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('description', models.TextField(blank=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-start_date']},
        ),
        migrations.CreateModel(
            name='Feedback360',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relationship', models.CharField(choices=[('MANAGER', 'Manager'), ('PEER', 'Peer'), ('DIRECT_REPORT', 'Direct Report'), ('SELF', 'Self')], default='PEER', max_length=20)),
                ('rating', models.DecimalField(decimal_places=1, max_digits=3)),
                ('comments', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('from_employee', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='feedback_given', to=settings.AUTH_USER_MODEL)),
                ('performance_review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback_entries', to='hr_management.performancereview')),
                ('to_employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback_received', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='CandidateResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField()),
                ('score', models.PositiveIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='hr_management.candidateprofile')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hr_management.recruitmentquestion')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='TrainingEnrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('ASSIGNED', 'Assigned'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed')], default='ASSIGNED', max_length=20)),
                ('completion_percentage', models.PositiveIntegerField(default=0)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='training_enrollments', to=settings.AUTH_USER_MODEL)),
                ('training_program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='hr_management.trainingprogram')),
            ],
            options={'ordering': ['-created_at'], 'unique_together': {('training_program', 'employee')}},
        ),
    ]
