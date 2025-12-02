from django.urls import path
from . import views

urlpatterns = [
    # Employee CRUD operations
    path('', views.EmployeeListCreateAPIView.as_view(), name='employee-list-create'),
    path('<int:pk>/', views.EmployeeDetailAPIView.as_view(), name='employee-detail'),
    
    # Employee profile (for logged-in employee)
    path('my-profile/', views.EmployeeProfileAPIView.as_view(), name='my-employee-profile'),
    
    # Position management
    path('positions/', views.PositionListCreateAPIView.as_view(), name='position-list-create'),
    path('positions/<int:pk>/', views.PositionDetailAPIView.as_view(), name='position-detail'),
    
    # Employee documents
    path('<int:employee_id>/documents/', views.EmployeeDocumentListCreateAPIView.as_view(), name='employee-document-list-create'),
    path('<int:employee_id>/documents/<int:pk>/', views.EmployeeDocumentDetailAPIView.as_view(), name='employee-document-detail'),
    
    # Employee notes (HR only)
    path('<int:employee_id>/notes/', views.EmployeeNoteListCreateAPIView.as_view(), name='employee-note-list-create'),
    path('<int:employee_id>/notes/<int:pk>/', views.EmployeeNoteDetailAPIView.as_view(), name='employee-note-detail'),
    
    # Statistics and bulk operations
    path('statistics/', views.employee_statistics, name='employee-statistics'),
    path('bulk-update/', views.bulk_update_employees, name='bulk-update-employees'),
]