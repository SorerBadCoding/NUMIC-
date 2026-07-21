from django.db import models


class Event(models.Model):
    """One-off calendar items: exams, deadlines, holidays, university events,
    and per-occurrence overrides (cancel / no-class-today) for a recurring
    ClassSection. Regular weekly classes themselves are generated on the fly
    from ClassSection and are not stored here.
    """

    class EventType(models.TextChoices):
        MIDTERM = "midterm", "Midterm Exam"
        FINAL = "final", "Final Exam"
        DEADLINE = "deadline", "Assignment Deadline"
        HOLIDAY = "holiday", "Holiday"
        UNIVERSITY_EVENT = "university_event", "University Event"
        CLASS_CANCELLED = "class_cancelled", "Class Cancelled"

    COLORS = {
        EventType.MIDTERM: "#f59e0b",
        EventType.FINAL: "#ef4444",
        EventType.DEADLINE: "#8b5cf6",
        EventType.HOLIDAY: "#10b981",
        EventType.UNIVERSITY_EVENT: "#0ea5e9",
        EventType.CLASS_CANCELLED: "#94a3b8",
    }

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_all_day = models.BooleanField(default=False)

    subject = models.ForeignKey("academics.Subject", on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="events")
    section = models.ForeignKey("academics.ClassSection", on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="overrides",
                                 help_text="Set together with occurrence_date for CLASS_CANCELLED events")
    occurrence_date = models.DateField(null=True, blank=True,
                                        help_text="The specific date of the class occurrence being cancelled")
    room = models.ForeignKey("campus.Room", on_delete=models.SET_NULL, null=True, blank=True)

    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self):
        return f"{self.get_event_type_display()}: {self.title}"

    @property
    def color(self):
        return self.COLORS.get(self.event_type, "#3b82f6")
