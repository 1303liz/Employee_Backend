from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class RecruitmentQuestion(models.Model):
    CATEGORY_CHOICES = [
        ('TECHNICAL', 'Technical'),
        ('BEHAVIORAL', 'Behavioral'),
        ('EXPERIENCE', 'Experience'),
        ('GENERAL', 'General'),
    ]

    question = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERAL')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_category_display()}: {self.question[:50]}"


class CandidateProfile(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('UNDER_REVIEW', 'Under Review'),
        ('SHORTLISTED', 'Shortlisted'),
        ('REJECTED', 'Rejected'),
    ]

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=50, blank=True)
    position_applied = models.CharField(max_length=120)
    resume_link = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.position_applied}"


class CandidateResponse(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(RecruitmentQuestion, on_delete=models.CASCADE)
    answer = models.TextField()
    score = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Response by {self.candidate.full_name}"


class TrainingProgram(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.title


class TrainingEnrollment(models.Model):
    STATUS_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]

    training_program = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE, related_name='enrollments')
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='training_enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED')
    completion_percentage = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['training_program', 'employee']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.username} - {self.training_program.title}"


class PerformanceReview(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('FINALIZED', 'Finalized'),
    ]

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reviews_conducted')
    review_period = models.CharField(max_length=50)
    overall_rating = models.DecimalField(max_digits=3, decimal_places=1)
    strengths = models.TextField(blank=True)
    improvement_areas = models.TextField(blank=True)
    goals = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.username} - {self.review_period}"


class Feedback360(models.Model):
    RELATIONSHIP_CHOICES = [
        ('MANAGER', 'Manager'),
        ('PEER', 'Peer'),
        ('DIRECT_REPORT', 'Direct Report'),
        ('SELF', 'Self'),
    ]

    performance_review = models.ForeignKey(PerformanceReview, on_delete=models.CASCADE, related_name='feedback_entries')
    from_employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='feedback_given')
    to_employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedback_received')
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, default='PEER')
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"360 Feedback for {self.to_employee.username} ({self.relationship})"


class TrainingApplication(models.Model):
    """Allows an employee to self-apply for an active training program."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    ]

    training_program = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='training_applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reason = models.TextField(blank=True, help_text='Why do you want to attend this training?')
    hr_notes = models.TextField(blank=True, help_text='HR decision notes')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['training_program', 'applicant']
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.username} → {self.training_program.title} [{self.status}]"


class PeerEvaluation(models.Model):
    """Employee-driven peer evaluation, independent of formal performance reviews."""
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluations_given'
    )
    evaluatee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluations_received'
    )
    period = models.CharField(max_length=50, help_text='Evaluation period, e.g. Q1 2026')
    communication_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    teamwork_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    technical_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    leadership_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    overall_comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['evaluator', 'evaluatee', 'period']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.evaluator.username} evaluated {self.evaluatee.username} [{self.period}]"

    @property
    def average_rating(self):
        return round(
            (self.communication_rating + self.teamwork_rating + self.technical_rating + self.leadership_rating) / 4,
            2,
        )
