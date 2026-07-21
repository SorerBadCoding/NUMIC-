from django.contrib import admin

from .models import ClassSection, Enrollment, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "credits")
    search_fields = ("code", "name")


@admin.register(ClassSection)
class ClassSectionAdmin(admin.ModelAdmin):
    list_display = ("subject", "teacher", "room", "weekday", "start_time", "end_time", "academic_term")
    list_filter = ("weekday", "academic_term", "year", "semester")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "section", "enrolled_on")
    search_fields = ("student__first_name", "student__last_name", "student__student_profile__student_id")
