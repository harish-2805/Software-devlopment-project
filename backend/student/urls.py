from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/',  views.dashboard,       name='student_dashboard'),
    path('academics/',  views.academics,        name='student_academics'),
    path('attendance/', views.attendance,       name='student_attendance'),
    path('messages/',   views.student_messages, name='student_messages'),
    path('alumni/',     views.alumni,           name='student_alumni'),
]