from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Employee Check-in/Check-out
    path('check-in/', views.CheckInAPIView.as_view(), name='check_in'),
    path('check-out/', views.CheckOutAPIView.as_view(), name='check_out'),
    path('break/start/', views.BreakStartAPIView.as_view(), name='break_start'),
    path('break/end/', views.BreakEndAPIView.as_view(), name='break_end'),
    
    # Attendance Records
    path('records/', views.AttendanceRecordListAPIView.as_view(), name='attendance_list'),
    path('records/<int:pk>/', views.AttendanceRecordDetailAPIView.as_view(), name='attendance_detail'),
    path('my/today/', views.MyTodayAttendanceAPIView.as_view(), name='my_today_attendance'),
    path('my/history/', views.MyAttendanceHistoryAPIView.as_view(), name='my_attendance_history'),
    path('my/summary/', views.my_attendance_summary, name='my_attendance_summary'),
    
    # Schedule Management
    path('schedules/', views.WorkScheduleListCreateAPIView.as_view(), name='schedule_list'),
    path('employee-schedules/', views.EmployeeScheduleListCreateAPIView.as_view(), name='employee_schedule_list'),
    
    # Policy and Holiday Management
    path('policies/', views.AttendancePolicyListCreateAPIView.as_view(), name='policy_list'),
    path('holidays/', views.HolidayListCreateAPIView.as_view(), name='holiday_list'),
    
    # Reports and Statistics (HR Only)
    path('statistics/', views.attendance_statistics, name='attendance_statistics'),
    path('reports/generate/', views.generate_attendance_report, name='generate_report'),
]