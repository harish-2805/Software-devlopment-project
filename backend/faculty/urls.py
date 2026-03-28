from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
]