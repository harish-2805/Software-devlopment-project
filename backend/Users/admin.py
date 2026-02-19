from django.contrib import admin
from .models import User, Student, Faculty, Department

admin.site.register(User)
admin.site.register(Student)
admin.site.register(Faculty)
admin.site.register(Department)
