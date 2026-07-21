from django.contrib import admin

from .models import AttendanceAttempt, AttendanceRecord, AttendanceSession, QRToken


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ("section", "date", "opened_by", "is_active")
    list_filter = ("is_active", "date")


@admin.register(QRToken)
class QRTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "session", "created_at", "expires_at", "is_consumed")
    list_filter = ("is_consumed",)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "marked_at", "distance_meters")
    search_fields = ("student__first_name", "student__last_name")


@admin.register(AttendanceAttempt)
class AttendanceAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "result", "attempted_at")
    list_filter = ("result",)
