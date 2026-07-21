from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.attendance_home, name="home"),
    path("session/<int:section_id>/", views.teacher_session, name="teacher_session"),
    path("session/<int:session_id>/qr.json", views.qr_json, name="qr_json"),
    path("session/<int:session_id>/roster.json", views.roster_json, name="roster_json"),
    path("session/<int:session_id>/close/", views.close_session, name="close_session"),
    path("scan/", views.scan_view, name="scan"),
    path("submit/", views.submit_attendance, name="submit"),
]
