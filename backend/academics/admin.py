from django.contrib import admin
from .models import Subject, Enrollment, Marks, Attendance

admin.site.register(Subject)
admin.site.register(Enrollment)
admin.site.register(Marks)
admin.site.register(Attendance)