from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date, timedelta


def default_expiry_date():
    """Default expiry date for leave recommendations (30 days from today)"""
    return date.today() + timedelta(days=30)


class AttendancePrediction(models.Model):
    """AI-based attendance predictions for employees"""
    PREDICTION_TYPES = [
        ('DAILY', 'Daily Prediction'),
        ('WEEKLY', 'Weekly Prediction'),
        ('MONTHLY', 'Monthly Prediction'),
    ]
    
    RISK_LEVELS = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Risk'),
    ]
    
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendance_predictions')
    prediction_type = models.CharField(max_length=10, choices=PREDICTION_TYPES, default='DAILY')
    prediction_date = models.DateField()
    
    # Prediction metrics
    attendance_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Probability of attendance (0-1)"
    )
    lateness_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Probability of being late (0-1)"
    )
    absence_risk = models.CharField(max_length=10, choices=RISK_LEVELS, default='LOW')
    
    # Contributing factors (JSON field to store various factors)
    contributing_factors = models.JSONField(
        default=dict,
        help_text="Factors contributing to the prediction (historical patterns, seasonality, etc.)"
    )
    
    # Model metrics
    model_confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.7,
        help_text="Confidence level of the AI model"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['employee', 'prediction_type', 'prediction_date']
        ordering = ['-prediction_date', 'employee']
    
    def __str__(self):
        return f"{self.employee.username} - {self.prediction_type} prediction for {self.prediction_date}"


class MoodAnalysis(models.Model):
    """Employee mood analysis based on various data points"""
    MOOD_SCORES = [
        ('VERY_NEGATIVE', 'Very Negative'),
        ('NEGATIVE', 'Negative'),
        ('NEUTRAL', 'Neutral'),
        ('POSITIVE', 'Positive'),
        ('VERY_POSITIVE', 'Very Positive'),
    ]
    
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mood_analyses')
    analysis_date = models.DateField(default=date.today)
    
    # Mood metrics
    mood_score = models.FloatField(
        validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)],
        help_text="Overall mood score from -1 (very negative) to 1 (very positive)"
    )
    mood_category = models.CharField(max_length=15, choices=MOOD_SCORES)
    
    # Detailed analysis
    stress_level = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Stress level from 0 (no stress) to 1 (high stress)"
    )
    engagement_level = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Engagement level from 0 (disengaged) to 1 (highly engaged)"
    )
    satisfaction_level = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Job satisfaction from 0 (unsatisfied) to 1 (highly satisfied)"
    )
    
    # Analysis details
    data_sources = models.JSONField(
        default=list,
        help_text="List of data sources used for analysis"
    )
    analysis_factors = models.JSONField(
        default=dict,
        help_text="Detailed breakdown of factors affecting mood"
    )
    
    # Recommendations
    recommendations = models.TextField(
        blank=True,
        help_text="AI-generated recommendations for mood improvement"
    )
    
    # Flags for HR attention
    requires_attention = models.BooleanField(default=False)
    attention_reason = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['employee', 'analysis_date']
        ordering = ['-analysis_date', 'employee']
    
    def __str__(self):
        return f"{self.employee.username} - Mood: {self.mood_category} on {self.analysis_date}"


class LeaveRecommendation(models.Model):
    """Smart leave recommendations based on AI analysis"""
    RECOMMENDATION_TYPES = [
        ('OPTIMAL_TIMING', 'Optimal Timing'),
        ('BURNOUT_PREVENTION', 'Burnout Prevention'),
        ('TEAM_COORDINATION', 'Team Coordination'),
        ('WORKLOAD_BALANCE', 'Workload Balance'),
        ('WELLNESS', 'Wellness Recommendation'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('HIGH', 'High Priority'),
        ('URGENT', 'Urgent'),
    ]
    
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')
    
    # Recommendation details
    recommended_start_date = models.DateField()
    recommended_end_date = models.DateField()
    recommended_duration = models.PositiveIntegerField(help_text="Recommended leave duration in days")
    
    # Analysis data
    reasoning = models.TextField(help_text="AI reasoning for this recommendation")
    benefits = models.JSONField(
        default=list,
        help_text="List of expected benefits from taking this leave"
    )
    risk_factors = models.JSONField(
        default=list,
        help_text="Potential risk factors if leave is not taken"
    )
    
    # Supporting metrics
    current_workload_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.5,
        help_text="Current workload intensity (0-1)"
    )
    burnout_risk_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.0,
        help_text="Risk of burnout (0-1)"
    )
    team_impact_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.5,
        help_text="Impact on team if leave is taken (lower is better)"
    )
    
    # Alternative suggestions
    alternative_dates = models.JSONField(
        default=list,
        help_text="Alternative date ranges for the leave"
    )
    
    # Status tracking
    is_active = models.BooleanField(default=True)
    was_acted_upon = models.BooleanField(default=False)
    employee_feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at', 'employee']
    
    def __str__(self):
        return f"{self.employee.username} - {self.recommendation_type} ({self.priority})"
    
    @property
    def is_expired(self):
        """Check if recommendation is expired"""
        return self.recommended_start_date < date.today()
    
    def save(self, *args, **kwargs):
        """Override save to calculate duration if not provided"""
        if self.recommended_start_date and self.recommended_end_date:
            self.recommended_duration = (self.recommended_end_date - self.recommended_start_date).days + 1
        super().save(*args, **kwargs)
