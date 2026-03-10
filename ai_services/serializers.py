from rest_framework import serializers
from django.contrib.auth.models import User
from .models import AttendancePrediction, MoodAnalysis, LeaveRecommendation


class AttendancePredictionSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_username = serializers.CharField(source='employee.username', read_only=True)
    
    class Meta:
        model = AttendancePrediction
        fields = [
            'id', 'employee', 'employee_name', 'employee_username',
            'prediction_type', 'prediction_date', 'attendance_probability',
            'lateness_probability', 'absence_risk', 'contributing_factors',
            'model_confidence', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MoodAnalysisSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_username = serializers.CharField(source='employee.username', read_only=True)
    
    class Meta:
        model = MoodAnalysis
        fields = [
            'id', 'employee', 'employee_name', 'employee_username',
            'analysis_date', 'mood_score', 'mood_category', 'stress_level',
            'engagement_level', 'satisfaction_level', 'data_sources',
            'analysis_factors', 'recommendations', 'requires_attention',
            'attention_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LeaveRecommendationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_username = serializers.CharField(source='employee.username', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = LeaveRecommendation
        fields = [
            'id', 'employee', 'employee_name', 'employee_username',
            'recommendation_type', 'priority', 'recommended_start_date',
            'recommended_end_date', 'recommended_duration', 'reasoning',
            'benefits', 'risk_factors', 'current_workload_score',
            'burnout_risk_score', 'team_impact_score', 'alternative_dates',
            'is_active', 'was_acted_upon', 'employee_feedback',
            'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_expired(self, obj):
        """Check if recommendation is expired (past recommended start date)"""
        from datetime import date
        return obj.recommended_start_date < date.today() if obj.recommended_start_date else False


# Summary serializers for lightweight views
class AttendancePredictionSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for summary views"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    
    class Meta:
        model = AttendancePrediction
        fields = [
            'id', 'employee', 'employee_name', 'prediction_date',
            'attendance_probability', 'absence_risk', 'model_confidence'
        ]


class MoodAnalysisSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for summary views"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    
    class Meta:
        model = MoodAnalysis
        fields = [
            'id', 'employee', 'employee_name', 'analysis_date',
            'mood_score', 'mood_category', 'requires_attention'
        ]


class LeaveRecommendationSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for summary views"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    
    class Meta:
        model = LeaveRecommendation
        fields = [
            'id', 'employee', 'employee_name', 'recommendation_type',
            'priority', 'recommended_start_date', 'recommended_duration',
            'burnout_risk_score', 'is_active'
        ]