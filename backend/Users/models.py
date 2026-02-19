from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES= (
        ('student','Student'),
        ('faculty','Faculty')
    )

    role = models.CharField(max_length=10,choices=ROLE_CHOICES)

class YearChoices(models.IntegerChoices):
    FIRST = 1,'First Year'
    SECOND = 2,'Second Year'
    THIRD = 3, 'Third Year'
    FOURTH = 4,'Fourth Year'

class SemChoices(models.IntegerChoices):
    SEM1 = 1, 'Semester 1'
    SEM2 = 2, 'Semester 2'
    SEM3 = 3, 'Semester 3'
    SEM4 = 4, 'Semester 4'
    SEM5 = 5, 'Semester 5'
    SEM6 = 6, 'Semester 6'
    SEM7 = 7, 'Semester 7'
    SEM8 = 8, 'Semester 8'

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)

    roll_no = models.CharField(max_length=6,unique=True)
    year = models.IntegerField(choices=YearChoices.choices)
    semester = models.IntegerField(choices=SemChoices.choices)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    # to display user to admin....it will shothat obj..user name
    def __str__(self):
      return self.user.username
    
class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    emp_id = models.CharField(max_length=6, unique=True)

    def __str__(self):
        return self.user.username