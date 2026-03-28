from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from academics.models import Subject


@login_required
def faculty_dashboard(request):
    if request.user.role != 'faculty':
        return redirect('login')
    faculty = request.user.faculty
    subjects = Subject.objects.filter(faculty=faculty)
    return render(request, 'faculty/faculty_dashboard.html', {
        'faculty': faculty,
        'subjects': subjects,
    })