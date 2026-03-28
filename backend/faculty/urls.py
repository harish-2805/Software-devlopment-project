from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/',   views.faculty_dashboard,  name='faculty_dashboard'),
    path('attendance/',  views.faculty_attendance,  name='faculty_attendance'),
    path('marks/',       views.faculty_marks,        name='faculty_marks'),
    path('messages/',    views.faculty_messages,     name='faculty_messages'),
    path('profile/',     views.faculty_profile,      name='faculty_profile'),
]
