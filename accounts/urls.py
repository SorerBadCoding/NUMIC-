from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.dashboard_redirect, name="dashboard_redirect"),
    path("login/", views.NumLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("student-id/", views.student_id_card_view, name="student_id_card"),
]
