from django.db import models


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    pinned = models.BooleanField(default=False)
    audience_major = models.CharField(max_length=120, blank=True, help_text="Leave blank for all majors")
    audience_year = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Leave blank for all years")
    subject = models.ForeignKey("academics.Subject", on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="announcements",
                                 help_text="Leave blank for a university-wide announcement")

    class Meta:
        ordering = ["-pinned", "-created_at"]

    def __str__(self):
        return self.title


class Notification(models.Model):
    class NotifType(models.TextChoices):
        CLASS_CANCELLED = "class_cancelled", "Class Cancelled"
        EXAM_REMINDER = "exam_reminder", "Exam Reminder"
        DEADLINE_REMINDER = "deadline_reminder", "Assignment Due"
        ATTENDANCE = "attendance", "Attendance Recorded"
        SCHEDULE_UPDATED = "schedule_updated", "Schedule Updated"
        ANNOUNCEMENT = "announcement", "Announcement"
        GENERAL = "general", "General"

    ICONS = {
        NotifType.CLASS_CANCELLED: "🚫",
        NotifType.EXAM_REMINDER: "📝",
        NotifType.DEADLINE_REMINDER: "⏰",
        NotifType.ATTENDANCE: "✅",
        NotifType.SCHEDULE_UPDATED: "🔄",
        NotifType.ANNOUNCEMENT: "📢",
        NotifType.GENERAL: "🔔",
    }

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="notifications")
    notif_type = models.CharField(max_length=25, choices=NotifType.choices, default=NotifType.GENERAL)
    title = models.CharField(max_length=200)
    body = models.CharField(max_length=255, blank=True)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.title}"

    @property
    def icon(self):
        return self.ICONS.get(self.notif_type, "🔔")
