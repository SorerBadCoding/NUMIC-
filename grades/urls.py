from django.urls import path

from . import views

app_name = "grades"

urlpatterns = [
    path("", views.grades_view, name="view"),
    path("teacher/", views.teacher_classes_view, name="teacher_classes"),
    path("teacher/section/<int:section_id>/", views.gradebook_view, name="gradebook"),
    path("teacher/section/<int:section_id>/save/", views.gradebook_save, name="gradebook_save"),
]
