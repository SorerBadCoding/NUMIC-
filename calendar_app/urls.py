from django.urls import path

from . import views

app_name = "calendar_app"

urlpatterns = [
    path("", views.calendar_view, name="view"),
    path("events.json", views.events_json, name="events_json"),
    path("events/create/", views.event_create, name="event_create"),
    path("events/<int:event_id>/delete/", views.event_delete, name="event_delete"),
    path("occurrence/cancel/", views.cancel_occurrence, name="cancel_occurrence"),
    path("occurrence/restore/", views.restore_occurrence, name="restore_occurrence"),
    path("sections/room/", views.change_room, name="change_room"),
    path("sections/create/", views.section_create, name="section_create"),
]
