from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils.dateparse import parse_date
from django.db import models
from datetime import date, timedelta
import logging

from .models import AttendancePrediction, MoodAnalysis, LeaveRecommendation
from .serializers import AttendancePredictionSerializer, MoodAnalysisSerializer, LeaveRecommendationSerializer
from .ai_engine import AttendancePredictionService, MoodAnalysisService, LeaveRecommendationService, AIServiceManager

logger = logging.getLogger(__name__)


# Attendance Prediction Views
class AttendancePredictionListView(generics.ListAPIView):
    """List attendance predictions for employees"""
    serializer_class = AttendancePredictionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = AttendancePrediction.objects.all()
        
        # Filter by employee if specified
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(prediction_date__gte=parse_date(start_date))
        if end_date:
            queryset = queryset.filter(prediction_date__lte=parse_date(end_date))
        
        # Filter by risk level
        risk_level = self.request.query_params.get('risk_level')
        if risk_level:
            queryset = queryset.filter(absence_risk=risk_level.upper())
        
        return queryset.order_by('-prediction_date', 'employee__username')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_attendance_prediction(request):
    """Generate attendance prediction for a specific employee"""
    try:
        employee_id = request.data.get('employee_id')
        prediction_date = request.data.get('prediction_date')
        
        if not employee_id:
            return Response(
                {'error': 'employee_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = User.objects.get(id=employee_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Parse prediction date
        pred_date = None
        if prediction_date:
            pred_date = parse_date(prediction_date)
            if not pred_date:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Generate prediction
        service = AttendancePredictionService()
        prediction = service.predict_attendance(employee, pred_date)
        
        return Response({
            'employee': employee.username,
            'employee_name': employee.get_full_name(),
            'prediction_date': pred_date or (date.today() + timedelta(days=1)),
            'prediction': prediction,
            'message': 'Attendance prediction generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating attendance prediction: {str(e)}")
        return Response(
            {'error': 'Failed to generate prediction'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_prediction_dashboard(request):
    """Dashboard data for attendance predictions"""
    try:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # Get tomorrow's predictions
        tomorrow_predictions = AttendancePrediction.objects.filter(
            prediction_date=tomorrow
        ).select_related('employee')
        
        # Statistics
        total_predictions = tomorrow_predictions.count()
        high_risk_count = tomorrow_predictions.filter(absence_risk='HIGH').count()
        medium_risk_count = tomorrow_predictions.filter(absence_risk='MEDIUM').count()
        low_risk_count = tomorrow_predictions.filter(absence_risk='LOW').count()
        
        # High risk employees
        high_risk_employees = AttendancePredictionSerializer(
            tomorrow_predictions.filter(absence_risk='HIGH')[:10], 
            many=True
        ).data
        
        return Response({
            'date': tomorrow,
            'statistics': {
                'total_predictions': total_predictions,
                'high_risk': high_risk_count,
                'medium_risk': medium_risk_count,
                'low_risk': low_risk_count
            },
            'high_risk_employees': high_risk_employees,
            'average_attendance_probability': tomorrow_predictions.aggregate(
                avg_prob=models.Avg('attendance_probability')
            )['avg_prob'] or 0
        })
        
    except Exception as e:
        logger.error(f"Error getting attendance dashboard data: {str(e)}")
        return Response(
            {'error': 'Failed to get dashboard data'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Mood Analysis Views
class MoodAnalysisListView(generics.ListAPIView):
    """List mood analyses for employees"""
    serializer_class = MoodAnalysisSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = MoodAnalysis.objects.all()
        
        # Filter by employee if specified
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(analysis_date__gte=parse_date(start_date))
        if end_date:
            queryset = queryset.filter(analysis_date__lte=parse_date(end_date))
        
        # Filter by mood category
        mood_category = self.request.query_params.get('mood_category')
        if mood_category:
            queryset = queryset.filter(mood_category=mood_category.upper())
        
        # Filter employees requiring attention
        requires_attention = self.request.query_params.get('requires_attention')
        if requires_attention and requires_attention.lower() == 'true':
            queryset = queryset.filter(requires_attention=True)
        
        return queryset.order_by('-analysis_date', 'employee__username')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_employee_mood(request):
    """Analyze mood for a specific employee"""
    try:
        employee_id = request.data.get('employee_id')
        analysis_date = request.data.get('analysis_date')
        
        if not employee_id:
            return Response(
                {'error': 'employee_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = User.objects.get(id=employee_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Parse analysis date
        anal_date = None
        if analysis_date:
            anal_date = parse_date(analysis_date)
            if not anal_date:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Analyze mood
        service = MoodAnalysisService()
        analysis = service.analyze_employee_mood(employee, anal_date)
        
        return Response({
            'employee': employee.username,
            'employee_name': employee.get_full_name(),
            'analysis_date': anal_date or date.today(),
            'analysis': analysis,
            'message': 'Mood analysis completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error analyzing employee mood: {str(e)}")
        return Response(
            {'error': 'Failed to analyze mood'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mood_analysis_dashboard(request):
    """Dashboard data for mood analysis"""
    try:
        today = date.today()
        
        # Recent mood analyses (last 30 days)
        recent_analyses = MoodAnalysis.objects.filter(
            analysis_date__gte=today - timedelta(days=30)
        ).select_related('employee')
        
        # Statistics
        total_analyses = recent_analyses.count()
        requires_attention = recent_analyses.filter(requires_attention=True).count()
        
        # Mood distribution
        from django.db.models import Count
        mood_distribution = recent_analyses.values('mood_category').annotate(
            count=Count('mood_category')
        )
        
        # Employees requiring attention
        attention_employees = MoodAnalysisSerializer(
            recent_analyses.filter(requires_attention=True).order_by('-analysis_date')[:10], 
            many=True
        ).data
        
        # Average scores
        from django.db.models import Avg
        averages = recent_analyses.aggregate(
            avg_mood=Avg('mood_score'),
            avg_stress=Avg('stress_level'),
            avg_engagement=Avg('engagement_level'),
            avg_satisfaction=Avg('satisfaction_level')
        )
        
        return Response({
            'date_range': {
                'start': today - timedelta(days=30),
                'end': today
            },
            'statistics': {
                'total_analyses': total_analyses,
                'requires_attention': requires_attention,
                'attention_percentage': (requires_attention / max(total_analyses, 1)) * 100
            },
            'mood_distribution': list(mood_distribution),
            'average_scores': averages,
            'attention_employees': attention_employees
        })
        
    except Exception as e:
        logger.error(f"Error getting mood dashboard data: {str(e)}")
        return Response(
            {'error': 'Failed to get dashboard data'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Leave Recommendation Views
class LeaveRecommendationListView(generics.ListAPIView):
    """List leave recommendations for employees"""
    serializer_class = LeaveRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = LeaveRecommendation.objects.filter(is_active=True)
        
        # Filter by employee if specified
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority.upper())
        
        # Filter by recommendation type
        rec_type = self.request.query_params.get('type')
        if rec_type:
            queryset = queryset.filter(recommendation_type=rec_type.upper())
        
        return queryset.order_by('-priority', 'recommended_start_date')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_leave_recommendations(request):
    """Generate leave recommendations for a specific employee"""
    try:
        employee_id = request.data.get('employee_id')
        
        if not employee_id:
            return Response(
                {'error': 'employee_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = User.objects.get(id=employee_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate recommendations
        service = LeaveRecommendationService()
        recommendations = service.generate_leave_recommendation(employee)
        
        return Response({
            'employee': employee.username,
            'employee_name': employee.get_full_name(),
            'analysis_date': date.today(),
            'recommendations': recommendations,
            'message': 'Leave recommendations generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating leave recommendations: {str(e)}")
        return Response(
            {'error': 'Failed to generate recommendations'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leave_recommendation_dashboard(request):
    """Dashboard data for leave recommendations"""
    try:
        # Active recommendations
        active_recommendations = LeaveRecommendation.objects.filter(is_active=True)
        
        # Statistics
        total_recommendations = active_recommendations.count()
        urgent_count = active_recommendations.filter(priority='URGENT').count()
        high_count = active_recommendations.filter(priority='HIGH').count()
        
        # Priority distribution
        from django.db.models import Count
        priority_distribution = active_recommendations.values('priority').annotate(
            count=Count('priority')
        )
        
        # Type distribution
        type_distribution = active_recommendations.values('recommendation_type').annotate(
            count=Count('recommendation_type')
        )
        
        # High priority recommendations
        high_priority = LeaveRecommendationSerializer(
            active_recommendations.filter(priority__in=['URGENT', 'HIGH']).order_by('-priority')[:10], 
            many=True
        ).data
        
        # Average scores
        from django.db.models import Avg
        averages = active_recommendations.aggregate(
            avg_workload=Avg('current_workload_score'),
            avg_burnout=Avg('burnout_risk_score'),
            avg_team_impact=Avg('team_impact_score')
        )
        
        return Response({
            'statistics': {
                'total_recommendations': total_recommendations,
                'urgent_count': urgent_count,
                'high_count': high_count
            },
            'priority_distribution': list(priority_distribution),
            'type_distribution': list(type_distribution),
            'average_scores': averages,
            'high_priority_recommendations': high_priority
        })
        
    except Exception as e:
        logger.error(f"Error getting leave recommendations dashboard data: {str(e)}")
        return Response(
            {'error': 'Failed to get dashboard data'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_recommendation_feedback(request, recommendation_id):
    """Update employee feedback on leave recommendation"""
    try:
        try:
            recommendation = LeaveRecommendation.objects.get(id=recommendation_id)
        except LeaveRecommendation.DoesNotExist:
            return Response(
                {'error': 'Recommendation not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        feedback = request.data.get('feedback', '')
        was_acted_upon = request.data.get('was_acted_upon', False)
        
        recommendation.employee_feedback = feedback
        recommendation.was_acted_upon = was_acted_upon
        if was_acted_upon:
            recommendation.is_active = False
        recommendation.save()
        
        return Response({
            'message': 'Recommendation feedback updated successfully',
            'recommendation_id': recommendation_id
        })
        
    except Exception as e:
        logger.error(f"Error updating recommendation feedback: {str(e)}")
        return Response(
            {'error': 'Failed to update feedback'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Combined AI Analysis Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_comprehensive_analysis(request):
    """Run comprehensive AI analysis for an employee"""
    try:
        employee_id = request.data.get('employee_id')
        
        if not employee_id:
            return Response(
                {'error': 'employee_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = User.objects.get(id=employee_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Employee not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Run all AI services
        manager = AIServiceManager()
        results = manager.run_daily_analysis(employee)
        
        return Response({
            'employee': employee.username,
            'employee_name': employee.get_full_name(),
            'analysis_date': date.today(),
            'results': results,
            'message': 'Comprehensive AI analysis completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error running comprehensive analysis: {str(e)}")
        return Response(
            {'error': 'Failed to run comprehensive analysis'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_daily_analysis_all(request):
    """Run daily AI analysis for all employees"""
    try:
        # Check if user has permission (HR or admin)
        if not (request.user.is_staff or 
                hasattr(request.user, 'employeeprofile') and 
                request.user.employeeprofile.role in ['HR', 'MANAGER']):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        manager = AIServiceManager()
        results = manager.run_daily_analysis()
        
        return Response({
            'analysis_date': date.today(),
            'results': results,
            'message': f'Daily AI analysis completed for {results["processed_employees"]} employees'
        })
        
    except Exception as e:
        logger.error(f"Error running daily analysis for all employees: {str(e)}")
        return Response(
            {'error': 'Failed to run daily analysis'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# AI Dashboard Overview
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_services_overview(request):
    """Get overview of all AI services"""
    try:
        today = date.today()
        
        # Attendance predictions overview
        attendance_predictions = AttendancePrediction.objects.filter(
            prediction_date=today + timedelta(days=1)
        ).count()
        
        # Mood analyses overview
        recent_mood_analyses = MoodAnalysis.objects.filter(
            analysis_date__gte=today - timedelta(days=7)
        ).count()
        
        mood_attention_required = MoodAnalysis.objects.filter(
            analysis_date__gte=today - timedelta(days=7),
            requires_attention=True
        ).count()
        
        # Leave recommendations overview
        active_leave_recs = LeaveRecommendation.objects.filter(is_active=True).count()
        urgent_leave_recs = LeaveRecommendation.objects.filter(
            is_active=True, 
            priority='URGENT'
        ).count()
        
        return Response({
            'overview_date': today,
            'attendance_predictions': {
                'total_predictions_tomorrow': attendance_predictions,
            },
            'mood_analysis': {
                'recent_analyses': recent_mood_analyses,
                'attention_required': mood_attention_required
            },
            'leave_recommendations': {
                'active_recommendations': active_leave_recs,
                'urgent_recommendations': urgent_leave_recs
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting AI services overview: {str(e)}")
        return Response(
            {'error': 'Failed to get overview'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
