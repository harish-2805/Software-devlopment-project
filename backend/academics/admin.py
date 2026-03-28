from django.contrib import admin
from .models import Subject, Enrollment, Marks, Attendance, Message, Alumni,Backlog


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

@admin.register(Backlog)
class BacklogAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'attempt_number', 'status', 'payment_status', 'registration_date']
    list_filter = ['status', 'payment_status', 'subject__department']
    search_fields = ['student__user__username', 'subject__name', 'student__roll_no']
    readonly_fields = ['registration_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'subject', 'attempt_number')
        }),
        ('Registration Details', {
            'fields': ('registration_date', 'exam_date', 'status')
        }),
        ('Payment Information', {
            'fields': ('payment_status', 'payment_id', 'amount')
        }),
        ('Results', {
            'fields': ('result_marks', 'result_grade', 'result_grade_points')
        }),
        ('Additional', {
            'fields': ('remarks',)
        }),
    )