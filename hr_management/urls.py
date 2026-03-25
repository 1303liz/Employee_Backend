from django.urls import path

from . import views


urlpatterns = [
    # Recruitment
    path('recruitment/questions/', views.RecruitmentQuestionListCreateAPIView.as_view(), name='recruitment-question-list-create'),
    path('recruitment/candidates/', views.CandidateListCreateAPIView.as_view(), name='candidate-list-create'),
    path('recruitment/candidates/<int:pk>/', views.CandidateDetailAPIView.as_view(), name='candidate-detail'),
    path('recruitment/candidates/<int:candidate_id>/responses/', views.CandidateResponseListCreateAPIView.as_view(), name='candidate-response-list-create'),
    path('recruitment/candidates/<int:candidate_id>/shortlist/', views.CandidateShortlistAPIView.as_view(), name='candidate-shortlist'),

    # Training & Development (HR)
    path('training/programs/', views.TrainingProgramListCreateAPIView.as_view(), name='training-program-list-create'),
    path('training/enrollments/', views.TrainingEnrollmentListCreateAPIView.as_view(), name='training-enrollment-list-create'),
    path('training/enrollments/<int:pk>/', views.TrainingEnrollmentDetailAPIView.as_view(), name='training-enrollment-detail'),
    # HR application management
    path('training/applications/', views.HRTrainingApplicationListView.as_view(), name='hr-training-application-list'),
    path('training/applications/<int:pk>/', views.HRTrainingApplicationDetailView.as_view(), name='hr-training-application-detail'),

    # Training & Development (Employee-facing)
    path('training/available/', views.AvailableTrainingProgramsView.as_view(), name='training-available'),
    path('training/my-applications/', views.TrainingApplicationListCreateView.as_view(), name='my-training-applications'),
    path('training/my-applications/<int:pk>/', views.TrainingApplicationDetailView.as_view(), name='my-training-application-detail'),
    path('training/my-enrollments/', views.MyTrainingEnrollmentsView.as_view(), name='my-training-enrollments'),
    path('training/my-enrollments/<int:pk>/', views.MyTrainingEnrollmentDetailView.as_view(), name='my-training-enrollment-detail'),

    # Performance Management and 360 (HR)
    path('performance/reviews/', views.PerformanceReviewListCreateAPIView.as_view(), name='performance-review-list-create'),
    path('performance/reviews/<int:pk>/', views.PerformanceReviewDetailAPIView.as_view(), name='performance-review-detail'),
    path('performance/reports/employee/', views.employee_performance_report, name='employee-performance-report'),
    path('performance/feedback-360/', views.Feedback360ListCreateAPIView.as_view(), name='feedback-360-list-create'),
    path('performance/reviews/<int:review_id>/feedback-summary/', views.feedback_360_summary, name='feedback-360-summary'),

    # Peer Evaluations (Employee-facing)
    path('performance/peer-evaluations/', views.PeerEvaluationListCreateView.as_view(), name='peer-evaluation-list-create'),
    path('performance/peer-evaluations/<int:pk>/', views.PeerEvaluationDetailView.as_view(), name='peer-evaluation-detail'),

    # My Performance Report (Employee-facing)
    path('performance/my-report/', views.my_performance_report, name='my-performance-report'),
    path('performance/notifications/my-alerts/', views.my_employee_alerts, name='my-employee-alerts'),
]
