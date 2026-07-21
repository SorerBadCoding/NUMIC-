from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Achievement, StudentProfile, TeacherProfile, User


@admin.register(User)
class NumUserAdmin(UserAdmin):
    list_display = ("username", "get_full_name", "email", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("NUM Portal", {"fields": ("role", "phone", "avatar")}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("student_id", "user", "major", "year", "semester")
    search_fields = ("student_id", "user__first_name", "user__last_name")
    list_filter = ("major", "year", "semester")


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("staff_id", "user", "department", "title")
    search_fields = ("staff_id", "user__first_name", "user__last_name")


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "awarded_on")
    list_filter = ("awarded_on",)
