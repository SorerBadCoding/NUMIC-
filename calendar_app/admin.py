from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "event_type", "start_datetime", "end_datetime", "created_by")
    list_filter = ("event_type",)
    search_fields = ("title",)
