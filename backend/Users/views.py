from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, Student, Faculty, Department
from academics.models import Subject, Enrollment


def register_view(request):
    departments = Department.objects.all()

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        role = request.POST['role']
        email = request.POST.get('email', '')
        roll_no = request.POST.get('roll_no', '')
        year = request.POST.get('year', '')
        semester = request.POST.get('semester', '')
        emp_id = request.POST.get('emp_id', '')

        if password != confirm_password:
            return render(request, 'users/register.html', {
                'error': 'Passwords do not match!',
                'departments': departments
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'users/register.html', {
                'error': 'Username already exists!',
                'departments': departments
            })

        student_dept_id = request.POST.get('student_department')
        faculty_dept_id = request.POST.get('faculty_department')
        department_id = student_dept_id if role == 'student' else faculty_dept_id
        department = Department.objects.filter(id=department_id).first() if department_id else None

        if role == 'student':
            if not department:
                return render(request, 'users/register.html', {
                    'error': 'Please select a department',
                    'departments': departments
                })
            if not roll_no or not year or not semester:
                return render(request, 'users/register.html', {
                    'error': 'All student fields are required',
                    'departments': departments
                })

        if role == 'faculty':
            if not department:
                return render(request, 'users/register.html', {
                    'error': 'Please select a department',
                    'departments': departments
                })
            if not emp_id:
                return render(request, 'users/register.html', {
                    'error': 'Employee ID is required',
                    'departments': departments
                })

        user = User.objects.create_user(
            username=username,
            password=password,
            role=role,
            email=email
        )

        if role == 'student':
            student = Student.objects.create(
                user=user,
                roll_no=roll_no,
                year=year,
                semester=semester,
                department=department
            )
            # Auto-enroll into subjects for their dept + semester
            subjects = Subject.objects.filter(department=department, semester=semester)
            for subject in subjects:
                Enrollment.objects.get_or_create(student=student, subject=subject)

        elif role == 'faculty':
            Faculty.objects.create(user=user, department=department, emp_id=emp_id)

        return redirect('login')

    return render(request, 'users/register.html', {'departments': departments})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']

        user = authenticate(request, username=username, password=password)

        if user is not None and user.role == role:
            login(request, user)
            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'faculty':
                return redirect('faculty_dashboard')
        else:
            return render(request, 'users/login.html', {
                'error': 'Invalid credentials or role mismatch'
            })

    return render(request, 'users/login.html')


# NEW: Logout view — uses Django's built-in logout function
def logout_view(request):
    logout(request)
    return redirect('login')
