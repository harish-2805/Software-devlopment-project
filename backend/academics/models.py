from django.db import models
from users.models import Student, Department, Faculty
import math
from django.core.validators import MinValueValidator, MaxValueValidator

class Subject(models.Model):
    name       = models.CharField(max_length=100)
    code       = models.CharField(max_length=10, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    faculty    = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)
    year       = models.IntegerField()
    semester   = models.IntegerField()
    credits    = models.IntegerField(default=3)   # NEW — credits per subject

    def __str__(self):
        return f"{self.name} ({self.code})"


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student} enrolled in {self.subject}"

    class Meta:
        unique_together = ('student', 'subject')


# ─────────────────────────────────────────────
# RELATIVE GRADING ENGINE
# ─────────────────────────────────────────────

def round_half_down(value):
    """
    NIT AP rule: if fraction is exactly 0.5, round DOWN.
    Python's round() uses banker's rounding, so we implement manually.
    """
    floor_val = math.floor(value)
    if value - floor_val == 0.5:
        return floor_val          # round down on exactly 0.5
    return round(value)


def calculate_pass_threshold_cam(cam_marks_list):
    """
    35% of highest CAM in class.
    cam_marks_list: list of all students' CAM marks in this subject.
    """
    if not cam_marks_list:
        return 0
    highest = max(cam_marks_list)
    return round_half_down(highest * 0.35)


def calculate_pass_threshold_ese(ese_marks_list):
    """
    min(35% of highest ESE,  50% of class avg ESE)
    ese_marks_list: list of all students' ESE marks in this subject.
    """
    if not ese_marks_list:
        return 0
    highest    = max(ese_marks_list)
    threshold1 = round_half_down(highest * 0.35)

    avg        = sum(ese_marks_list) / len(ese_marks_list)
    threshold2 = round_half_down(avg * 0.50)

    return min(threshold1, threshold2)


def assign_relative_grades(subject):
    """
    Main function — calculates and saves grades for ALL students in a subject.
    Called automatically when faculty submits marks for a subject.

    Steps:
    1. Collect all marks for this subject
    2. Determine pass/fail for each student
    3. For passed students with class > 10: relative grading using μ and σ
    4. For class <= 10: all passed get P
    5. Save grade back to each Marks record
    """
    all_marks = Marks.objects.filter(subject=subject).select_related('student')

    if not all_marks.exists():
        return

    # Collect raw marks lists for threshold calculation
    cam_list = [m.cam for m in all_marks]
    ese_list = [m.ese for m in all_marks]

    cam_threshold = calculate_pass_threshold_cam(cam_list)
    ese_threshold = calculate_pass_threshold_ese(ese_list)

    # Step 1: Separate passed and failed students
    passed_marks = []
    for m in all_marks:
        if m.cam >= cam_threshold and m.ese >= ese_threshold:
            passed_marks.append(m)
        else:
            m.grade        = 'F'
            m.grade_points = 0
            m.save(update_fields=['grade', 'grade_points'])

    if not passed_marks:
        return

    # Step 2: Relative grading for passed students
    class_size = len(passed_marks)

    if class_size > 10:
        # Use mean and std deviation of TOTAL marks of passed students
        totals     = [m.total for m in passed_marks]
        mean       = sum(totals) / len(totals)
        variance   = sum((t - mean) ** 2 for t in totals) / len(totals)
        std_dev    = math.sqrt(variance)

        for m in passed_marks:
            t = m.total
            if   t >= mean + 2   * std_dev: grade = 'EX'
            elif t >= mean + 1.5 * std_dev: grade = 'A'
            elif t >= mean + 1   * std_dev: grade = 'B'
            elif t >= mean + 0.5 * std_dev: grade = 'C'
            elif t >= mean:                 grade = 'D'
            else:                           grade = 'P'

            grade_point_map = {'EX': 10, 'A': 9, 'B': 8, 'C': 7, 'D': 6, 'P': 5}
            m.grade        = grade
            m.grade_points = grade_point_map[grade]
            m.save(update_fields=['grade', 'grade_points'])
    else:
        # Class size <= 10: all passed students get P grade
        for m in passed_marks:
            m.grade        = 'P'
            m.grade_points = 5
            m.save(update_fields=['grade', 'grade_points'])


def calculate_sgpa(student, semester):
    """
    SGPA = Σ(credits × grade_points) / Σcredits
    For a given student and semester number.
    """
    marks_qs = Marks.objects.filter(
        student=student,
        subject__semester=semester
    ).select_related('subject')

    if not marks_qs.exists():
        return 0.0

    total_credit_points = sum(
        (m.grade_points or 0) * m.subject.credits
        for m in marks_qs
    )
    total_credits = sum(m.subject.credits for m in marks_qs)

    if total_credits == 0:
        return 0.0

    return round(total_credit_points / total_credits, 2)


def calculate_cgpa(student, up_to_semester):
    """
    CGPA = Σ(semester_credits × SGPA) / Σsemester_credits
    Calculated from semester 1 up to up_to_semester.
    Note: CGPA starts from I Year II Semester (sem 2) as per NIT AP rules.
    """
    if up_to_semester < 2:
        return 0.0

    total_weighted = 0.0
    total_credits  = 0

    for sem in range(1, up_to_semester + 1):
        sem_marks = Marks.objects.filter(
            student=student,
            subject__semester=sem
        ).select_related('subject')

        sem_credits = sum(m.subject.credits for m in sem_marks)
        if sem_credits == 0:
            continue

        sgpa = calculate_sgpa(student, sem)
        total_weighted += sgpa * sem_credits
        total_credits  += sem_credits

    if total_credits == 0:
        return 0.0

    return round(total_weighted / total_credits, 2)

from django.db import models
from users.models import Student, Department, Faculty
import math
from django.core.validators import MinValueValidator, MaxValueValidator

class Subject(models.Model):
    name       = models.CharField(max_length=100)
    code       = models.CharField(max_length=10, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    faculty    = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)
    year       = models.IntegerField()
    semester   = models.IntegerField()
    credits    = models.IntegerField(default=3)   # NEW — credits per subject

    def __str__(self):
        return f"{self.name} ({self.code})"


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student} enrolled in {self.subject}"

    class Meta:
        unique_together = ('student', 'subject')


# ─────────────────────────────────────────────
# RELATIVE GRADING ENGINE
# ─────────────────────────────────────────────

def round_half_down(value):
    floor_val = math.floor(value)
    if value - floor_val == 0.5:
        return floor_val
    return round(value)


def calculate_pass_threshold_cam(cam_marks_list):
    if not cam_marks_list:
        return 0
    highest = max(cam_marks_list)
    return round_half_down(highest * 0.35)


def calculate_pass_threshold_ese(ese_marks_list):
    if not ese_marks_list:
        return 0
    highest    = max(ese_marks_list)
    threshold1 = round_half_down(highest * 0.35)

    avg        = sum(ese_marks_list) / len(ese_marks_list)
    threshold2 = round_half_down(avg * 0.50)

    return min(threshold1, threshold2)


def assign_relative_grades(subject):
    all_marks = Marks.objects.filter(subject=subject).select_related('student')

    if not all_marks.exists():
        return

    cam_list = [m.cam for m in all_marks]
    ese_list = [m.ese or 0 for m in all_marks]

    cam_threshold = calculate_pass_threshold_cam(cam_list)
    ese_threshold = calculate_pass_threshold_ese(ese_list)

    passed_marks = []
    for m in all_marks:
        if m.cam >= cam_threshold and (m.ese or 0) >= ese_threshold:
            passed_marks.append(m)
        else:
            m.grade = 'F'
            m.grade_points = 0
            m.save(update_fields=['grade', 'grade_points'])

    if not passed_marks:
        return

    class_size = len(passed_marks)

    if class_size > 10:
        totals = [m.total for m in passed_marks]
        mean = sum(totals) / len(totals)
        variance = sum((t - mean) ** 2 for t in totals) / len(totals)
        std_dev = math.sqrt(variance)

        for m in passed_marks:
            t = m.total

            if   t >= mean + 2   * std_dev: grade = 'EX'
            elif t >= mean + 1.5 * std_dev: grade = 'A'
            elif t >= mean + 1   * std_dev: grade = 'B'
            elif t >= mean + 0.5 * std_dev: grade = 'C'
            elif t >= mean:                 grade = 'D'
            else:                           grade = 'P'

            gp = {'EX':10,'A':9,'B':8,'C':7,'D':6,'P':5}

            m.grade = grade
            m.grade_points = gp[grade]
            m.save(update_fields=['grade', 'grade_points'])
    else:
        for m in passed_marks:
            m.grade = 'P'
            m.grade_points = 5
            m.save(update_fields=['grade', 'grade_points'])


# ─────────────────────────────────────────────
# SGPA / CGPA (UNCHANGED)
# ─────────────────────────────────────────────

def calculate_sgpa(student, semester):

    marks_qs = Marks.objects.filter(
        student=student,
        subject__semester=semester
    ).select_related('subject')

    if not marks_qs.exists():
        return 0.0

    total_credit_points = sum(
        (m.grade_points or 0) * m.subject.credits
        for m in marks_qs
    )
    total_credits = sum(m.subject.credits for m in marks_qs)

    if total_credits == 0:
        return 0.0

    return round(total_credit_points / total_credits, 2)


def calculate_cgpa(student, up_to_semester):

    if up_to_semester < 2:
        return 0.0

    total_weighted = 0.0
    total_credits  = 0

    for sem in range(1, up_to_semester + 1):

        sem_marks = Marks.objects.filter(
            student=student,
            subject__semester=sem
        ).select_related('subject')

        sem_credits = sum(m.subject.credits for m in sem_marks)
        if sem_credits == 0:
            continue

        sgpa = calculate_sgpa(student, sem)
        total_weighted += sgpa * sem_credits
        total_credits  += sem_credits

    if total_credits == 0:
        return 0.0

    return round(total_weighted / total_credits, 2)


# ─────────────────────────────────────────────
# MARKS MODEL (ENHANCED — LIVE RELATIVE SYSTEM)
# ─────────────────────────────────────────────

class Marks(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

# CAM components (total CAM = 50)
    minor1 = models.IntegerField(default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)])

    midsem = models.IntegerField(default=0,
        validators=[MinValueValidator(0), MaxValueValidator(30)])

    minor2 = models.IntegerField(default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)])

    # ESE (may not be conducted yet)
    ese = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(50)]
    )

    total = models.IntegerField(blank=True, null=True)
    grade = models.CharField(max_length=3, blank=True, null=True)
    grade_points = models.IntegerField(default=0)

    # ───────── LIVE SCORE ─────────

    @property
    def cam(self):
        return self.minor1 + self.midsem + self.minor2

    @property
    def running_score(self):
        """Marks till current stage"""
        return (
            (self.minor1 or 0) +
            (self.midsem or 0) +
            (self.minor2 or 0) +
            (self.ese or 0)
        )

    # ───────── PREDICTED RELATIVE GRADE ─────────

    @property
    def predicted_grade(self):

        all_marks = Marks.objects.filter(subject=self.subject)
        scores = [m.running_score for m in all_marks]

        if len(scores) <= 1:
            return None

        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = math.sqrt(variance)

        t = self.running_score

        if std_dev == 0:
            return "P"

        if   t >= mean + 2*std_dev: return "EX"
        elif t >= mean + 1.5*std_dev: return "A"
        elif t >= mean + 1*std_dev: return "B"
        elif t >= mean + 0.5*std_dev: return "C"
        elif t >= mean: return "D"
        else: return "P"

    # ───────── CLASS RANK ─────────

    @property
    def current_rank(self):
        all_marks = Marks.objects.filter(subject=self.subject)
        ordered = sorted(all_marks, key=lambda m: m.running_score, reverse=True)

        for idx, m in enumerate(ordered, start=1):
            if m.id == self.id:
                return idx
        return None

    # ───────── AT RISK DETECTION ─────────

    @property
    def is_at_risk(self):
        """Student likely to fail relative grading"""
        grade = self.predicted_grade
        return grade in ["P", None]

    # ───────── SAVE ─────────

    def save(self, *args, **kwargs):

        self.total = self.cam + (self.ese or 0)
        super().save(*args, **kwargs)

        update_fields = kwargs.get('update_fields')
        if update_fields is None:
            assign_relative_grades(self.subject)

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.grade or 'ungraded'}"

    class Meta:
        unique_together = ('student', 'subject')
        
# ─────────────────────────────────────────────
# ATTENDANCE MODEL
# ─────────────────────────────────────────────

class Attendance(models.Model):
    student          = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject          = models.ForeignKey(Subject, on_delete=models.CASCADE)
    attended_classes = models.IntegerField(default=0)
    total_classes    = models.IntegerField(default=0)

    @property
    def percentage(self):
        if self.total_classes == 0:
            return 0
        return round((self.attended_classes / self.total_classes) * 100, 1)

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.percentage}%"

    class Meta:
        unique_together = ('student', 'subject')


# ─────────────────────────────────────────────
# MESSAGE MODEL
# ─────────────────────────────────────────────

class Message(models.Model):
    sender    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sent_messages')
    receiver  = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='received_messages')
    subject   = models.CharField(max_length=200)
    body      = models.TextField()
    reply     = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read   = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} to {self.receiver}: {self.subject}"

    class Meta:
        ordering = ['-timestamp']


# ─────────────────────────────────────────────
# ALUMNI MODEL
# ─────────────────────────────────────────────

class Alumni(models.Model):
    name         = models.CharField(max_length=100)
    department   = models.ForeignKey(Department, on_delete=models.CASCADE)
    batch_year   = models.IntegerField()
    company      = models.CharField(max_length=100, blank=True)
    designation  = models.CharField(max_length=100, blank=True)
    linkedin_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.batch_year})"

    class Meta:
        ordering = ['-batch_year']