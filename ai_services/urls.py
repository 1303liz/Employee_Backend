from django.urls import path
from . import views

app_name = 'ai_services'

urlpatterns = [
    # AI Services Overview
    path('overview/', views.ai_services_overview, name='ai_services_overview'),
    
    # Attendance Prediction URLs
    path('attendance/predictions/', views.AttendancePredictionListView.as_view(), name='attendance_predictions_list'),
    path('attendance/predict/', views.generate_attendance_prediction, name='generate_attendance_prediction'),
    path('attendance/dashboard/', views.attendance_prediction_dashboard, name='attendance_prediction_dashboard'),
    
    # Mood Analysis URLs
    path('mood/analyses/', views.MoodAnalysisListView.as_view(), name='mood_analyses_list'),
    path('mood/analyze/', views.analyze_employee_mood, name='analyze_employee_mood'),
    path('mood/dashboard/', views.mood_analysis_dashboard, name='mood_analysis_dashboard'),
    
    # Leave Recommendation URLs
    path('leave/recommendations/', views.LeaveRecommendationListView.as_view(), name='leave_recommendations_list'),
    path('leave/recommend/', views.generate_leave_recommendations, name='generate_leave_recommendations'),
    path('leave/dashboard/', views.leave_recommendation_dashboard, name='leave_recommendation_dashboard'),
    path('leave/recommendations/<int:recommendation_id>/feedback/', views.update_recommendation_feedback, name='update_recommendation_feedback'),
    
    # Comprehensive Analysis URLs
    path('analysis/comprehensive/', views.run_comprehensive_analysis, name='run_comprehensive_analysis'),
    path('analysis/daily-all/', views.run_daily_analysis_all, name='run_daily_analysis_all'),
]