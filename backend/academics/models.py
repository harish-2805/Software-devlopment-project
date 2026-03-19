from django.db import models
from users.models import Student,Department,Faculty

class Subject(models.Model):
  name = models.CharField(max_length=100)
  code = models.CharField(max_length=10,unique=True)
  department = models.ForeignKey(Department,on_delete=models.CASCADE)
  faculty = models.ForeignKey(Faculty,on_delete=models.SET_NULL,null=True)
  year = models.IntegerField()
  semester = models.IntegerField()

  def __str__(self):
    return self.name
  
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student} - {self.subject}"
    class Meta:
        unique_together = ('student', 'subject')
    
class Marks(models.Model):

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    semester = models.IntegerField()

    minor1 = models.IntegerField(default=0)
    midsem = models.IntegerField(default=0)
    minor2 = models.IntegerField(default=0)
    endsem = models.IntegerField(default=0)

    total = models.IntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.total = self.minor1 + self.midsem + self.minor2 + self.endsem
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('student', 'subject', 'semester')
    

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    attended_classes = models.IntegerField()
    total_classes = models.IntegerField()

    def __str__(self):
        return f"{self.student} - {self.subject}"

