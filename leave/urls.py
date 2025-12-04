from django.urls import path
from . import views

urlpatterns = [
    # Leave Types
    path('types/', views.LeaveTypeListCreateAPIView.as_view(), name='leave-type-list-create'),
    path('types/<int:pk>/', views.LeaveTypeDetailAPIView.as_view(), name='leave-type-detail'),
    
    # Leave Applications
    path('applications/', views.LeaveApplicationListCreateAPIView.as_view(), name='leave-application-list-create'),
    path('applications/<int:pk>/', views.LeaveApplicationDetailAPIView.as_view(), name='leave-application-detail'),
    path('applications/<int:pk>/approve/', views.LeaveApplicationApprovalAPIView.as_view(), name='leave-application-approve'),
    
    # Leave Balances
    path('balances/', views.LeaveBalanceListAPIView.as_view(), name='leave-balance-list'),
    path('my-balances/', views.MyLeaveBalanceAPIView.as_view(), name='my-leave-balance'),
    
    # Attachments
    path('applications/<int:leave_app_id>/attachments/', views.LeaveApplicationAttachmentListCreateAPIView.as_view(), name='leave-attachment-list-create'),
    
    # Comments
    path('applications/<int:leave_app_id>/comments/', views.LeaveApplicationCommentListCreateAPIView.as_view(), name='leave-comment-list-create'),
    
    # Statistics and Reports
    path('statistics/', views.leave_statistics, name='leave-statistics'),
    path('my-summary/', views.my_leave_summary, name='my-leave-summary'),
    path('bulk-approve/', views.bulk_approve_leaves, name='bulk-approve-leaves'),
    
    # Advanced Reports and Analytics
    path('reports/employee/', views.employee_leave_report, name='employee_leave_report'),
    path('reports/team/', views.team_leave_report, name='team_leave_report'),
    path('reports/analytics/', views.leave_analytics, name='leave_analytics'),
    path('reports/performance/', views.combined_performance_report, name='combined_performance_report'),
]