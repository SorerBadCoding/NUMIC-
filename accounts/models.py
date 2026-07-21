from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        TEACHER = "teacher", "Teacher"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=30, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    def __str__(self):
        return self.get_full_name() or self.username


class StudentProfile(models.Model):
    class Year(models.IntegerChoices):
        YEAR_1 = 1, "Year 1"
        YEAR_2 = 2, "Year 2"
        YEAR_3 = 3, "Year 3"
        YEAR_4 = 4, "Year 4"

    class Semester(models.IntegerChoices):
        SEM_1 = 1, "Semester 1"
        SEM_2 = 2, "Semester 2"

    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="student_profile")
    student_id = models.CharField(max_length=20, unique=True)
    major = models.CharField(max_length=120)
    year = models.IntegerField(choices=Year.choices, default=Year.YEAR_1)
    semester = models.IntegerField(choices=Semester.choices, default=Semester.SEM_1)
    enrolled_on = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["student_id"]

    def __str__(self):
        return f"{self.student_id} — {self.user.get_full_name()}"

    @property
    def year_semester_label(self):
        return f"Year {self.year} · Semester {self.semester}"


class TeacherProfile(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="teacher_profile")
    staff_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=120)
    title = models.CharField(max_length=80, default="Lecturer")

    def __str__(self):
        return f"{self.title} {self.user.get_full_name()}"


class Achievement(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="achievements")
    title = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=10, default="🏆")
    awarded_on = models.DateField()

    class Meta:
        ordering = ["-awarded_on"]

    def __str__(self):
        return self.title
