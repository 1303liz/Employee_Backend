from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('register/', views.RegisterAPIView.as_view(), name='register'),
    path('logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User management
    path('profile/', views.ProfileAPIView.as_view(), name='profile'),
    path('profile/detail/', views.ProfileDetailAPIView.as_view(), name='profile_detail'),
    path('profile/update/', views.ProfileUpdateAPIView.as_view(), name='profile_update'),
    path('profile/documents/', views.UserDocumentListCreateAPIView.as_view(), name='user_documents'),
    path('profile/documents/<int:pk>/', views.UserDocumentDetailAPIView.as_view(), name='user_document_detail'),
    path('change-password/', views.ChangePasswordAPIView.as_view(), name='change_password'),
    path('user-info/', views.user_info, name='user_info'),
    
    # Dashboard
    path('dashboard/', views.DashboardAPIView.as_view(), name='dashboard'),
    
    # Employee management (HR only)
    path('employees/', views.EmployeeListAPIView.as_view(), name='employee_list'),
    path('employees/<int:pk>/', views.EmployeeDetailAPIView.as_view(), name='employee_detail'),
    path('employees/stats/', views.employee_stats, name='employee_stats'),
    
    # Department management (HR only)
    path('departments/', views.DepartmentListAPIView.as_view(), name='department_list'),
    path('departments/<int:pk>/', views.DepartmentDetailAPIView.as_view(), name='department_detail'),
]