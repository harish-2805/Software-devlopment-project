from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from academics.models import (
    Marks, Attendance, Enrollment, Message, Alumni,
    calculate_sgpa, calculate_cgpa
)
from users.models import Faculty


@login_required
def dashboard(request):
    if request.user.role != 'student':
        return redirect('login')

    student    = request.user.student
    marks_qs   = Marks.objects.filter(student=student).select_related('subject')
    semester   = student.semester

    # SGPA for current semester
    sgpa = calculate_sgpa(student, semester)

    # CGPA across all semesters
    cgpa = calculate_cgpa(student, semester)

    # Backlogs = F grade subjects
    backlogs = marks_qs.filter(grade='F').count()

    # Overall attendance
    attendance_qs = Attendance.objects.filter(student=student)
    if attendance_qs.exists():
        total_attended = sum(a.attended_classes for a in attendance_qs)
        total_classes  = sum(a.total_classes    for a in attendance_qs)
        attendance_pct = round((total_attended / total_classes) * 100, 1) if total_classes > 0 else 0
    else:
        attendance_pct = 0

    # Department rank by total marks this semester
    from users.models import Student
    dept_students  = Student.objects.filter(
        department=student.department,
        semester=student.semester
    )
    student_totals = []
    for s in dept_students:
        s_total = sum(
            m.total or 0
            for m in Marks.objects.filter(student=s, subject__semester=semester)
        )
        student_totals.append((s.id, s_total))
    student_totals.sort(key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, (sid, _) in enumerate(student_totals) if sid == student.id), '-')

    # Chart data
    chart_labels = [m.subject.name for m in marks_qs]
    chart_data   = [m.total or 0   for m in marks_qs]

    return render(request, 'student/student_dashboard.html', {
        'student':        student,
        'sgpa':           sgpa,
        'cgpa':           cgpa,
        'backlogs':       backlogs,
        'attendance_pct': attendance_pct,
        'rank':           rank,
        'chart_labels':   chart_labels,
        'chart_data':     chart_data,
    })


@login_required
def academics(request):
    if request.user.role != 'student':
        return redirect('login')

    student  = request.user.student
    semester = student.semester
    marks_qs = Marks.objects.filter(
        student=student,
        subject__semester=semester
    ).select_related('subject')

    subjects_data = []
    for m in marks_qs:
        subjects_data.append({
        'subject':      m.subject.name,
        'code':         m.subject.code,
        'credits':      m.subject.credits,

        'minor1':       m.minor1,
        'midsem':       m.midsem,
        'minor2':       m.minor2,
        'cam':          m.cam,
        'ese':          m.ese,

        'total':        m.total or 0,
        'running_score': m.running_score,

        # FINAL grade (after ESE)
        'grade':        m.grade or '-',
        'grade_points': m.grade_points or 0,

        # ⭐ NEW FEATURES
        'predicted_grade': m.predicted_grade or '-',
        'marks_needed':    m.marks_needed_for_next_grade or '-',
        'rank':            m.current_rank or '-',
        'is_at_risk':      m.is_at_risk,
    })

    sgpa = calculate_sgpa(student, semester)
    cgpa = calculate_cgpa(student, semester)

    # Chart data — grouped bars per subject
    chart_labels = [s['subject'] for s in subjects_data]
    chart_minor1 = [s['minor1']  for s in subjects_data]
    chart_midsem = [s['midsem']  for s in subjects_data]
    chart_minor2 = [s['minor2']  for s in subjects_data]
    chart_ese    = [s['ese']     for s in subjects_data]

    return render(request, 'student/academics.html', {
        'student':       student,
        'subjects_data': subjects_data,
        'sgpa':          sgpa,
        'cgpa':          cgpa,
        'semester':      semester,
        'chart_labels':  chart_labels,
        'chart_minor1':  chart_minor1,
        'chart_midsem':  chart_midsem,
        'chart_minor2':  chart_minor2,
        'chart_ese':     chart_ese,
    })


@login_required
def attendance(request):
    if request.user.role != 'student':
        return redirect('login')

    student       = request.user.student
    attendance_qs = Attendance.objects.filter(student=student).select_related('subject')

    attendance_data = []
    for a in attendance_qs:
        pct    = a.percentage
        status = 'safe' if pct >= 80 else ('warning' if pct >= 60 else 'danger')
        attendance_data.append({
            'subject':    a.subject.name,
            'code':       a.subject.code,
            'attended':   a.attended_classes,
            'total':      a.total_classes,
            'percentage': pct,
            'status':     status,
        })

    total_att = sum(a['attended'] for a in attendance_data)
    total_cls = sum(a['total']    for a in attendance_data)
    overall   = round(total_att / total_cls * 100, 1) if total_cls > 0 else 0

    chart_labels   = [a['subject']  for a in attendance_data]
    chart_attended = [a['attended'] for a in attendance_data]
    chart_total    = [a['total']    for a in attendance_data]

    return render(request, 'student/attendance.html', {
        'student':         student,
        'attendance_data': attendance_data,
        'overall':         overall,
        'chart_labels':    chart_labels,
        'chart_attended':  chart_attended,
        'chart_total':     chart_total,
    })


@login_required
def student_messages(request):
    if request.user.role != 'student':
        return redirect('login')

    student      = request.user.student
    faculty_list = Faculty.objects.select_related('user', 'department').all()

    if request.method == 'POST':
        faculty_id = request.POST.get('faculty_id')
        subject    = request.POST.get('subject')
        body       = request.POST.get('body')

        if faculty_id and subject and body:
            faculty = Faculty.objects.get(id=faculty_id)
            Message.objects.create(
                sender=student, receiver=faculty,
                subject=subject, body=body
            )
            django_messages.success(request, 'Message sent successfully!')
            return redirect('student_messages')
        else:
            django_messages.error(request, 'All fields are required.')

    sent_messages = Message.objects.filter(
        sender=student
    ).select_related('receiver__user')

    return render(request, 'student/messages.html', {
        'student':       student,
        'faculty_list':  faculty_list,
        'sent_messages': sent_messages,
    })


@login_required
def alumni(request):
    if request.user.role != 'student':
        return redirect('login')

    student      = request.user.student
    dept_alumni  = Alumni.objects.filter(
        department=student.department
    ).order_by('-batch_year')
    other_alumni = Alumni.objects.exclude(
        department=student.department
    ).order_by('-batch_year')

    return render(request, 'student/alumni.html', {
        'student':       student,
        'dept_alumni':   dept_alumni,
        'other_alumni':  other_alumni,
    })

@login_required
def student_profile(request):
    if request.user.role != 'student':
        return redirect('login')
    student = request.user.student
    user    = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name  = request.POST.get('last_name', '').strip()
        user.email      = request.POST.get('email', '').strip()
        user.save()
        django_messages.success(request, 'Profile updated successfully!')
        return redirect('student_profile')
    return render(request, 'student/profile.html', {'student': student})
