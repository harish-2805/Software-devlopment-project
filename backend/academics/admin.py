from django.contrib import admin
from .models import Subject, Enrollment, Marks, Attendance, Message, Alumni


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'department', 'faculty', 'semester', 'year', 'credits']
    list_filter   = ['department', 'semester', 'year']
    search_fields = ['name', 'code']


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display  = ['student', 'subject', 'minor1', 'midsem', 'minor2', 'ese', 'total', 'grade', 'grade_points']
    list_filter   = ['subject__department', 'subject__semester', 'grade']
    search_fields = ['student__user__username', 'subject__name']
    readonly_fields = ['total', 'grade', 'grade_points']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display  = ['student', 'subject', 'attended_classes', 'total_classes', 'percentage']
    list_filter   = ['subject__department', 'subject__semester']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display  = ['student', 'subject']
    list_filter   = ['subject__department', 'subject__semester']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display  = ['sender', 'receiver', 'subject', 'timestamp', 'is_read']
    list_filter   = ['is_read']


@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display  = ['name', 'department', 'batch_year', 'company', 'designation']
    list_filter   = ['department', 'batch_year']
    search_fields = ['name', 'company']