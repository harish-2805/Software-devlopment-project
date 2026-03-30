from django.db import models
from users.models import Student, Department, Faculty
import math
from django.core.validators import MinValueValidator, MaxValueValidator

# ─────────────────────────────────────────────
# SUBJECT & ENROLLMENT MODELS (ONLY ONCE)
# ─────────────────────────────────────────────

class Subject(models.Model):
    name       = models.CharField(max_length=100)
    code       = models.CharField(max_length=10, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    faculty    = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)
    year       = models.IntegerField()
    semester   = models.IntegerField()
    credits    = models.IntegerField(default=3)

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
# RELATIVE GRADING ENGINE (DEFINE ONLY ONCE)
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
    """
    all_marks = Marks.objects.filter(subject=subject).select_related('student')

    print("Grading triggered")

    if not all_marks.exists():
        return

    # Collect raw marks lists for threshold calculation
    cam_list = [m.cam for m in all_marks]
    ese_list = [m.ese for m in all_marks if m.ese is not None]

    # Ensure ese_list has values for threshold calculation
    if not ese_list:
        ese_list = [0] * len(all_marks)

    cam_threshold = calculate_pass_threshold_cam(cam_list)
    ese_threshold = calculate_pass_threshold_ese(ese_list)

    # Step 1: Separate passed and failed students
    passed_marks = []
    for m in all_marks:
        ese_value = m.ese or 0
        if m.cam >= cam_threshold and ese_value >= ese_threshold:
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
            if std_dev == 0:
                grade = 'P'  
            elif   t >= mean + 1.5   * std_dev: grade = 'EX'
            elif t >= mean + 1 * std_dev: grade = 'A'
            elif t >= mean :               grade = 'B'
            elif t >= mean - 0.5 * std_dev: grade = 'C'
            elif t >= mean - 1 *std_dev:    grade = 'D'
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


# ─────────────────────────────────────────────
# SGPA / CGPA FUNCTIONS
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# MARKS MODEL (ONLY ONCE)
# ─────────────────────────────────────────────

class Marks(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    # CAM components (total CAM = 50)
    minor1 = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )

    midsem = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(30)]
    )

    minor2 = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )

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

        if   t >= mean + 1.5 * std_dev: return "EX"
        elif t >= mean + 1 * std_dev: return "A"
        elif t >= mean : return "B"
        elif t >= mean - 0.5 * std_dev: return "C"
        elif t >= mean - 1 * std_dev: return "D"
        else: return "P"

    # ───────── MARKS NEEDED FOR NEXT GRADE ─────────

    @property
    def marks_needed_for_next_grade(self):
        """
        Shows additional marks needed to reach next higher grade.
        Works dynamically with relative grading.
        """
        all_marks = Marks.objects.filter(subject=self.subject)
        scores = [m.running_score for m in all_marks]

        if len(scores) <= 1:
            return None

        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = math.sqrt(variance)

        current = self.running_score

        # Grade boundaries (LOW → HIGH)
        boundaries = [
            ("D",  mean - 1* std_dev),
            ("C",  mean - 0.5 * std_dev),
            ("B",  mean ),
            ("A",  mean + 1 * std_dev),
            ("EX", mean + 1.5 * std_dev),
        ]

        for grade, boundary in boundaries:
            if current < boundary:
                needed = math.ceil(boundary - current)
                return f"+{needed} marks for {grade}"

        # Already highest
        return "Highest Grade (EX)"

    # ───────── CLASS RANK ─────────

    @property
    def current_rank(self):
        all_marks = Marks.objects.filter(subject=self.subject)
        ordered = sorted(
            all_marks,
            key=lambda m: m.running_score,
            reverse=True
        )

        for idx, m in enumerate(ordered, start=1):
            if m.id == self.id:
                return idx
        return None

    # ───────── AT RISK DETECTION ─────────

    @property
    def is_at_risk(self):
        """At risk based on current grade - F, P, or D"""
        if self.grade in ['F', 'P', 'D']:
            return True
        return False
    
    # ───────── SAVE ─────────

    def save(self, *args, **kwargs):
        # auto total calculation
        self.total = self.cam + (self.ese or 0)
        
        # Get update_fields before super().save()
        update_fields = kwargs.get('update_fields')
        
        super().save(*args, **kwargs)

        # trigger grading engine (only if not updating specific fields)
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


# ─────────────────────────────────────────────
# BACKLOG MODEL
# ─────────────────────────────────────────────

class Backlog(models.Model):
    STATUS_CHOICES = [
        ('registered', 'Registered (Payment Pending)'),
        ('payment_verified', 'Payment Verified'),
        ('approved', 'Approved for Exam'),
        ('completed', 'Exam Completed'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('online', 'Online Payment'),
        ('offline', 'Offline (Bank Challan)'),
        ('pending', 'Payment Pending'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='backlogs')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    attempt_number = models.IntegerField(default=1)
    
    # Registration details
    registration_date = models.DateTimeField(auto_now_add=True)
    exam_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered')
    
    # Payment details
    payment_status = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='pending')
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_receipt = models.FileField(upload_to='backlog_receipts/', blank=True, null=True)
    amount = models.IntegerField(default=500)  # Backlog exam fee
    
    # Results
    result_marks = models.IntegerField(null=True, blank=True)
    result_grade = models.CharField(max_length=3, null=True, blank=True)
    result_grade_points = models.IntegerField(null=True, blank=True)
    
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-registration_date']
        unique_together = ['student', 'subject', 'attempt_number']
    
    def __str__(self):
        return f"{self.student} - {self.subject} (Attempt {self.attempt_number})"