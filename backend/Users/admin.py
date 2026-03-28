from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Student, Faculty, Department


# ================= USER ADMIN =================
class StudentInline(admin.StackedInline):
    model = Student
    extra = 0
    can_delete = False


class FacultyInline(admin.StackedInline):
    model = Faculty
    extra = 0
    can_delete = False


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff")

    fieldsets = UserAdmin.fieldsets + (
        ("Academic Info", {"fields": ("role",)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Academic Info", {"fields": ("role",)}),
    )

    search_fields = ("username", "email")
    ordering = ("username",)

    # show student/faculty details inside user page
    def get_inlines(self, request, obj=None):
        if obj:
            if obj.role == "student":
                return [StudentInline]
            elif obj.role == "faculty":
                return [FacultyInline]
        return []


# ================= STUDENT ADMIN =================
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("user", "roll_no", "department", "year", "semester")
    search_fields = ("user__username", "roll_no")
    list_filter = ("department", "year", "semester")


# ================= FACULTY ADMIN =================
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("user", "emp_id", "department")
    search_fields = ("user__username", "emp_id")
    list_filter = ("department",)


# ================= DEPARTMENT ADMIN =================
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)