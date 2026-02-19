from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import User, Student, Faculty, Department


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
        department_id = request.POST.get('department')
        emp_id = request.POST.get('emp_id', '')
        print(department_id)
        #  Password matches or not ... validation
        if password != confirm_password:
            return render(request, 'users/register.html', {
                'error': 'Passwords do not match!',
                'departments': departments
            })

        # checks if Username already exists..or not
        if User.objects.filter(username=username).exists():
            return render(request, 'users/register.html', {
                'error': 'Username already exists!',
                'departments': departments
            })

        # Get department safely
        student_dept_id = request.POST.get('student_department')
        faculty_dept_id = request.POST.get('faculty_department')

        department_id = None

        if role == 'student':
            department_id = student_dept_id
        elif role == 'faculty':
            department_id = faculty_dept_id

        department = None
        if department_id:
            department = Department.objects.filter(id=department_id).first()

        # Student validation
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

        # Faculty validation
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

        #  Create user after doing.....validation
        user = User.objects.create_user(
            username=username,
            password=password,
            role=role,
            email=email
        )

        #  Create one to one student or facluty based on role...
        if role == 'student':
            Student.objects.create(
                user=user,
                roll_no=roll_no,
                year=year,
                semester=semester,
                department=department
            )

        elif role == 'faculty':
            Faculty.objects.create(
                user=user,
                department=department,
                emp_id=emp_id
            )

        return redirect('login')

    return render(request, 'users/register.html', {'departments': departments})


def login_view(request):

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']
        # using inbuilt django based authetication....if user exist return it else ..none
        user = authenticate(request, username=username, password=password)

        if user is not None and user.role == role:
            login(request, user)

            if user.role == 'student':
                return redirect('student_dashboard')

            elif user.role == 'faculty':
                return redirect('faculty_dashboard')


        else:
            return render(request, 'users/login.html', {
                'error': 'Invalid credentials or role'
            })

    return render(request, 'users/login.html')


@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('login')
    return render(request, 'users/student_dashboard.html')


@login_required
def faculty_dashboard(request):
    if request.user.role != 'faculty':
        return redirect('login')
    return render(request, 'users/faculty_dashboard.html')
