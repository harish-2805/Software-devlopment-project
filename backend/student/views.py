from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.models import Student


@login_required
def dashboard(request):

    # Get logged-in student's profile
    student = request.user.student

    # Temporary values (you can calculate later)
    rank = 1
    total_marks = 0
    attendance_percentage = 0

    return render(request, 'student/student_dashboard.html', {
        'student': student,
        'rank': rank,
        'total_marks': total_marks,
        'attendance_percentage': attendance_percentage
    })

# student:student  is template_name and python object so we can access in insisde out html...