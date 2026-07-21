import uuid

from django.db import models
from django.utils import timezone


class AttendanceSession(models.Model):
    """A single day's attendance window for one ClassSection, opened by its teacher."""

    section = models.ForeignKey("academics.ClassSection", on_delete=models.CASCADE, related_name="attendance_sessions")
    date = models.DateField()
    opened_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="+")
    opened_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("section", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.section} — {self.date}"

    def close(self):
        self.is_active = False
        self.closed_at = timezone.now()
        self.save(update_fields=["is_active", "closed_at"])


class QRToken(models.Model):
    """A short-lived, single-use QR token minted for an AttendanceSession.

    Regenerated automatically every ATTENDANCE_QR_TTL_SECONDS. Consuming a
    token marks it used so a screenshot of it cannot be redeemed a second
    time, even within its validity window.
    """

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="tokens")
    token = models.CharField(max_length=64, unique=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_consumed = models.BooleanField(default=False)
    consumed_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.token[:8]}… ({self.session})"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    def is_valid(self):
        return self.is_active_session and not self.is_consumed and not self.is_expired

    @property
    def is_active_session(self):
        return self.session.is_active


class AttendanceRecord(models.Model):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records")
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="attendance_records")
    token = models.ForeignKey(QRToken, on_delete=models.SET_NULL, null=True, related_name="+")
    marked_at = models.DateTimeField(default=timezone.now)
    latitude = models.FloatField()
    longitude = models.FloatField()
    distance_meters = models.FloatField()
    device_timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("session", "student")
        ordering = ["-marked_at"]

    def __str__(self):
        return f"{self.student} present @ {self.session}"


class AttendanceAttempt(models.Model):
    """Audit log of every scan attempt, successful or not."""

    class Result(models.TextChoices):
        SUCCESS = "success", "Marked Present"
        EXPIRED_TOKEN = "expired_token", "QR Code Expired"
        INVALID_TOKEN = "invalid_token", "Invalid QR Code"
        ALREADY_CONSUMED = "already_consumed", "QR Code Already Used"
        OUT_OF_RANGE = "out_of_range", "Outside Campus Radius"
        OUTSIDE_TIME_WINDOW = "outside_time_window", "Outside Class Time Window"
        NOT_ENROLLED = "not_enrolled", "Not Enrolled In Subject"
        ALREADY_MARKED = "already_marked", "Attendance Already Recorded"
        SESSION_CLOSED = "session_closed", "Attendance Session Closed"

    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="attendance_attempts")
    session = models.ForeignKey(AttendanceSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="attempts")
    result = models.CharField(max_length=25, choices=Result.choices)
    detail = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    attempted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-attempted_at"]

    def __str__(self):
        return f"{self.student} — {self.get_result_display()}"
