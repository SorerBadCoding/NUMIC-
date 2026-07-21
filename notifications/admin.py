from django.contrib import admin

from .models import Announcement, Notification


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "created_at", "pinned")
    list_filter = ("pinned",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "notif_type", "title", "is_read", "created_at")
    list_filter = ("notif_type", "is_read")
