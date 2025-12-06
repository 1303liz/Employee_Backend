from django.urls import path
from . import views

urlpatterns = [
    # Work Schedules
    path('schedules/', views.WorkScheduleListCreateAPIView.as_view(), name='work-schedule-list-create'),
    path('schedules/<int:pk>/', views.WorkScheduleDetailAPIView.as_view(), name='work-schedule-detail'),
    
    # Employee Schedules
    path('employee-schedules/', views.EmployeeScheduleListCreateAPIView.as_view(), name='employee-schedule-list-create'),
    path('employee-schedules/<int:pk>/', views.EmployeeScheduleDetailAPIView.as_view(), name='employee-schedule-detail'),
    
    # Attendance Records
    path('records/', views.AttendanceRecordListAPIView.as_view(), name='attendance-record-list'),
    path('records/<int:pk>/', views.AttendanceRecordDetailAPIView.as_view(), name='attendance-record-detail'),
    
    # Check-in/Check-out
    path('check-in/', views.CheckInAPIView.as_view(), name='check-in'),
    path('check-out/', views.CheckOutAPIView.as_view(), name='check-out'),
    path('current-status/', views.current_attendance_status, name='current-status'),
    
    # Dashboard
    path('dashboard/', views.attendance_dashboard, name='attendance-dashboard'),
    
    # Holidays
    path('holidays/', views.HolidayListCreateAPIView.as_view(), name='holiday-list-create'),
    path('holidays/<int:pk>/', views.HolidayDetailAPIView.as_view(), name='holiday-detail'),
]
