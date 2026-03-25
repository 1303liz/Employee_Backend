from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    RecruitmentQuestion,
    CandidateProfile,
    CandidateResponse,
    TrainingProgram,
    TrainingEnrollment,
    TrainingApplication,
    PerformanceReview,
    Feedback360,
    PeerEvaluation,
)

User = get_user_model()


class RecruitmentQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentQuestion
        fields = ['id', 'question', 'category', 'is_active', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']


class CandidateResponseSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question', read_only=True)

    class Meta:
        model = CandidateResponse
        fields = ['id', 'candidate', 'question', 'question_text', 'answer', 'score', 'created_at']
        read_only_fields = ['created_at']


class CandidateProfileSerializer(serializers.ModelSerializer):
    responses = CandidateResponseSerializer(many=True, read_only=True)

    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'full_name', 'email', 'phone_number', 'position_applied',
            'resume_link', 'status', 'created_at', 'updated_at', 'responses'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TrainingProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingProgram
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'is_active', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']


class TrainingEnrollmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    program_title = serializers.CharField(source='training_program.title', read_only=True)

    class Meta:
        model = TrainingEnrollment
        fields = [
            'id', 'training_program', 'program_title', 'employee', 'employee_name',
            'status', 'completion_percentage', 'notes', 'created_at'
        ]
        read_only_fields = ['created_at']

    def get_employee_name(self, obj):
        full_name = obj.employee.get_full_name()
        return full_name if full_name else obj.employee.username


class PerformanceReviewSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceReview
        fields = [
            'id', 'employee', 'employee_name', 'reviewer', 'reviewer_name', 'review_period',
            'overall_rating', 'strengths', 'improvement_areas', 'goals',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reviewer', 'created_at', 'updated_at']

    def get_employee_name(self, obj):
        full_name = obj.employee.get_full_name()
        return full_name if full_name else obj.employee.username

    def get_reviewer_name(self, obj):
        if not obj.reviewer:
            return None
        full_name = obj.reviewer.get_full_name()
        return full_name if full_name else obj.reviewer.username


class Feedback360Serializer(serializers.ModelSerializer):
    from_employee_name = serializers.SerializerMethodField()
    to_employee_name = serializers.SerializerMethodField()

    class Meta:
        model = Feedback360
        fields = [
            'id', 'performance_review', 'from_employee', 'from_employee_name',
            'to_employee', 'to_employee_name', 'relationship', 'rating', 'comments', 'created_at'
        ]
        read_only_fields = ['from_employee', 'created_at']

    def get_from_employee_name(self, obj):
        if not obj.from_employee:
            return None
        full_name = obj.from_employee.get_full_name()
        return full_name if full_name else obj.from_employee.username

    def get_to_employee_name(self, obj):
        full_name = obj.to_employee.get_full_name()
        return full_name if full_name else obj.to_employee.username


class TrainingApplicationSerializer(serializers.ModelSerializer):
    applicant_name = serializers.SerializerMethodField()
    program_title = serializers.CharField(source='training_program.title', read_only=True)
    program_start_date = serializers.DateField(source='training_program.start_date', read_only=True)
    program_end_date = serializers.DateField(source='training_program.end_date', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TrainingApplication
        fields = [
            'id', 'training_program', 'program_title', 'program_start_date', 'program_end_date',
            'applicant', 'applicant_name', 'status', 'status_display',
            'reason', 'hr_notes', 'applied_at', 'updated_at',
        ]
        read_only_fields = ['applicant', 'status', 'hr_notes', 'applied_at', 'updated_at']

    def get_applicant_name(self, obj):
        full_name = obj.applicant.get_full_name()
        return full_name if full_name else obj.applicant.username


class TrainingApplicationHRSerializer(TrainingApplicationSerializer):
    """HR-facing serializer that allows updating status and hr_notes."""
    class Meta(TrainingApplicationSerializer.Meta):
        read_only_fields = ['applicant', 'applied_at']


class PeerEvaluationSerializer(serializers.ModelSerializer):
    evaluator_name = serializers.SerializerMethodField()
    evaluatee_name = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = PeerEvaluation
        fields = [
            'id', 'evaluator', 'evaluator_name', 'evaluatee', 'evaluatee_name',
            'period', 'communication_rating', 'teamwork_rating',
            'technical_rating', 'leadership_rating',
            'overall_comments', 'average_rating', 'created_at', 'updated_at',
        ]
        read_only_fields = ['evaluator', 'created_at', 'updated_at']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and attrs.get('evaluatee') == request.user:
            raise serializers.ValidationError({'evaluatee': 'You cannot evaluate yourself.'})
        return attrs

    def get_evaluator_name(self, obj):
        full_name = obj.evaluator.get_full_name()
        return full_name if full_name else obj.evaluator.username

    def get_evaluatee_name(self, obj):
        full_name = obj.evaluatee.get_full_name()
        return full_name if full_name else obj.evaluatee.username
