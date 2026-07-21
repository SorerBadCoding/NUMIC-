from django.db import models


class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    credits = models.PositiveSmallIntegerField(default=3)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class ClassSection(models.Model):
    """A recurring weekly class meeting for a subject, taught by one teacher."""

    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="sections")
    teacher = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True,
        related_name="teaching_sections", limit_choices_to={"role": "teacher"},
    )
    room = models.ForeignKey("campus.Room", on_delete=models.SET_NULL, null=True, related_name="sections")
    year = models.PositiveSmallIntegerField(default=1)
    semester = models.PositiveSmallIntegerField(default=1)
    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    academic_term = models.CharField(max_length=40, default="Spring 2026")

    class Meta:
        ordering = ["weekday", "start_time"]

    def __str__(self):
        return f"{self.subject.code} · {self.get_weekday_display()} {self.start_time:%H:%M}"

    @property
    def duration_label(self):
        return f"{self.start_time:%H:%M} - {self.end_time:%H:%M}"


class Enrollment(models.Model):
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="enrollments",
                                 limit_choices_to={"role": "student"})
    section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_on = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "section")

    def __str__(self):
        return f"{self.student} → {self.section}"


class Material(models.Model):
    section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=255, blank=True)
    url = models.URLField(blank=True)
    uploaded_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="+")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title
