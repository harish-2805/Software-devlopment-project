from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from academics.models import Subject, Marks, Attendance, Message, Enrollment
from users.models import Student


def faculty_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'faculty':
            return redirect('login')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def get_unread_count(faculty):
    return Message.objects.filter(receiver=faculty, is_read=False).count()


@faculty_required
def faculty_dashboard(request):
    faculty = request.user.faculty
    subjects = Subject.objects.filter(faculty=faculty)
    unread_count = get_unread_count(faculty)
    total_students = set()
    for subj in subjects:
        for enr in Enrollment.objects.filter(subject=subj):
            total_students.add(enr.student.id)
    return render(request, 'faculty/faculty_dashboard.html', {
        'faculty': faculty,
        'subjects': subjects,
        'unread_count': unread_count,
        'total_students': len(total_students),
    })


@faculty_required
def faculty_attendance(request):
    faculty = request.user.faculty
    subjects = Subject.objects.filter(faculty=faculty)
    selected_subject = None
    students_data = []
    subject_id = request.GET.get('subject_id') or request.POST.get('subject_id')
    if subject_id:
        selected_subject = get_object_or_404(Subject, id=subject_id, faculty=faculty)
        enrollments = Enrollment.objects.filter(subject=selected_subject).select_related('student__user')
        if request.method == 'POST' and 'save_attendance' in request.POST:
            for enr in enrollments:
                attended = request.POST.get(f'attended_{enr.student.id}', '0')
                total    = request.POST.get(f'total_{enr.student.id}', '0')
                try:
                    attended = max(0, int(attended))
                    total    = max(0, int(total))
                    if attended > total:
                        attended = total
                except ValueError:
                    attended, total = 0, 0
                att, _ = Attendance.objects.get_or_create(student=enr.student, subject=selected_subject)
                att.attended_classes = attended
                att.total_classes    = total
                att.save()
            django_messages.success(request, 'Attendance updated successfully!')
            return redirect(f'/faculty/attendance/?subject_id={subject_id}')
        for enr in enrollments:
            att = Attendance.objects.filter(student=enr.student, subject=selected_subject).first()
            students_data.append({
                'student':  enr.student,
                'attended': att.attended_classes if att else 0,
                'total':    att.total_classes    if att else 0,
                'pct':      att.percentage        if att else 0,
            })
    return render(request, 'faculty/faculty_attendance.html', {
        'faculty':          faculty,
        'subjects':         subjects,
        'selected_subject': selected_subject,
        'students_data':    students_data,
        'unread_count':     get_unread_count(faculty),
    })


@faculty_required
def faculty_marks(request):
    faculty = request.user.faculty
    subjects = Subject.objects.filter(faculty=faculty)
    selected_subject = None
    students_data = []
    subject_id = request.GET.get('subject_id') or request.POST.get('subject_id')
    if subject_id:
        selected_subject = get_object_or_404(Subject, id=subject_id, faculty=faculty)
        enrollments = Enrollment.objects.filter(subject=selected_subject).select_related('student__user')
        if request.method == 'POST' and 'save_marks' in request.POST:
            for enr in enrollments:
                sid = enr.student.id
                def get_int(field, default=0, _sid=sid):
                    try:
                        return int(request.POST.get(f'{field}_{_sid}', default))
                    except (ValueError, TypeError):
                        return default
                minor1 = min(max(get_int('minor1'), 0), 10)
                midsem = min(max(get_int('midsem'), 0), 30)
                minor2 = min(max(get_int('minor2'), 0), 10)
                ese_raw = request.POST.get(f'ese_{sid}', '').strip()
                ese = min(int(ese_raw), 50) if ese_raw.isdigit() else None
                marks, _ = Marks.objects.get_or_create(student=enr.student, subject=selected_subject)
                marks.minor1 = minor1
                marks.midsem = midsem
                marks.minor2 = minor2
                marks.ese    = ese
                marks.save()
            django_messages.success(request, 'Marks updated and grades recalculated!')
            return redirect(f'/faculty/marks/?subject_id={subject_id}')
        for enr in enrollments:
            marks = Marks.objects.filter(student=enr.student, subject=selected_subject).first()
            students_data.append({'student': enr.student, 'marks': marks})
    return render(request, 'faculty/faculty_marks.html', {
        'faculty':          faculty,
        'subjects':         subjects,
        'selected_subject': selected_subject,
        'students_data':    students_data,
        'unread_count':     get_unread_count(faculty),
    })


@faculty_required
def faculty_messages(request):
    faculty = request.user.faculty
    messages_qs = Message.objects.filter(receiver=faculty).select_related('sender__user').order_by('-timestamp')
    # Mark all as read on page visit
    messages_qs.filter(is_read=False).update(is_read=True)
    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        reply_text = request.POST.get('reply', '').strip()
        if message_id and reply_text:
            msg = get_object_or_404(Message, id=message_id, receiver=faculty)
            msg.reply   = reply_text
            msg.is_read = True
            msg.save()
            django_messages.success(request, 'Reply sent successfully!')
            return redirect('faculty_messages')
    return render(request, 'faculty/faculty_messages.html', {
        'faculty':     faculty,
        'messages_qs': messages_qs,
        'unread_count': 0,  # just visited, all marked read
    })


@faculty_required
def faculty_profile(request):
    faculty = request.user.faculty
    user    = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name  = request.POST.get('last_name', '').strip()
        user.email      = request.POST.get('email', '').strip()
        user.save()
        django_messages.success(request, 'Profile updated successfully!')
        return redirect('faculty_profile')
    return render(request, 'faculty/faculty_profile.html', {
        'faculty':      faculty,
        'unread_count': get_unread_count(faculty),
    })
