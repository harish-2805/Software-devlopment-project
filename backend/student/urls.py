from django.urls import path
from . import views

urlpatterns = [
    path('student-dashboard/', views.dashboard, name='student_dashboard'),
]
