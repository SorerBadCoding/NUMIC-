from django.urls import path

from . import views

app_name = "academics"

urlpatterns = [
    path("", views.subject_list, name="subject_list"),
    path("<int:subject_id>/", views.subject_detail, name="subject_detail"),
]
