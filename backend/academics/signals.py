from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Student, Subject, Enrollment


@receiver(post_save, sender=Student)
def auto_enroll_student(sender, instance, created, **kwargs):
    """
    Automatically enroll student into subjects
    when a new student is created.
    """

    # run only when NEW student is created
    if created:

        # subjects of student's dept + semester
        subjects = Subject.objects.filter(
            department=instance.department,
            semester=instance.semester
        )

        for subject in subjects:
            Enrollment.objects.get_or_create(
                student=instance,
                subject=subject
            )