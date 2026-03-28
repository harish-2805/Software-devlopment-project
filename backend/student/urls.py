from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/',  views.dashboard,        name='student_dashboard'),
    path('academics/',  views.academics,         name='student_academics'),
    path('attendance/', views.attendance,        name='student_attendance'),
    path('messages/',   views.student_messages,  name='student_messages'),
    path('alumni/',     views.alumni,             name='student_alumni'),
    path('profile/',    views.student_profile,   name='student_profile'),
        # Backlog URLs
    path('register-backlog/', views.register_backlog, name='register_backlog'),
    path('backlog-status/', views.backlog_status, name='backlog_status'),
    path('upload-receipt/', views.upload_receipt, name='upload_receipt'),
]
