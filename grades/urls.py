from django.urls import path

from . import views

app_name = "grades"

urlpatterns = [
    path("", views.grades_view, name="view"),
]
