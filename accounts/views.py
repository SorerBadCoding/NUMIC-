import json
from datetime import date

from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from academics.models import ClassSection, Enrollment, Subject
from attendance.models import AttendanceRecord, AttendanceSession
from attendance.qr import generate_qr_data_uri
from calendar_app.models import Event
from grades.models import compute_gpa
from notifications.models import Announcement

from .models import User


class NumLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


def logout_view(request):
    auth_logout(request)
    return redirect("accounts:login")


def _announcements_for(user):
    profile = getattr(user, "student_profile", None)
    qs = Announcement.objects.all()
    if profile:
        qs = qs.filter(Q(audience_major="") | Q(audience_major=profile.major)).filter(
            Q(audience_year__isnull=True) | Q(audience_year=profile.year)
        )
    return qs[:5]


@login_required
def dashboard_redirect(request):
    user = request.user
    if user.role == User.Role.TEACHER:
        return teacher_dashboard(request)
    if user.role == User.Role.ADMIN:
        return admin_dashboard(request)
    return student_dashboard(request)


def student_dashboard(request):
    user = request.user
    profile = user.student_profile
    now = timezone.localtime()
    today = now.date()
    weekday = today.weekday()

    enrollments = list(
        Enrollment.objects.filter(student=user)
        .select_related("section__subject", "section__room__building", "section__teacher")
    )
    section_ids = [e.section_id for e in enrollments]

    todays_sections = sorted(
        (e.section for e in enrollments if e.section.weekday == weekday),
        key=lambda s: s.start_time,
    )
    cancelled_today = set(
        Event.objects.filter(
            event_type=Event.EventType.CLASS_CANCELLED,
            section_id__in=section_ids,
            occurrence_date=today,
        ).values_list("section_id", flat=True)
    )
    for s in todays_sections:
        s.is_cancelled_today = s.id in cancelled_today

    upcoming_today_count = sum(
        1 for s in todays_sections if not s.is_cancelled_today and s.start_time >= now.time()
    )

    total_sessions = AttendanceSession.objects.filter(section_id__in=section_ids, date__lte=today).count()
    present_count = AttendanceRecord.objects.filter(student=user, session__section_id__in=section_ids).count()
    attendance_pct = round(present_count / total_sessions * 100) if total_sessions else None

    assignments_due = (
        Event.objects.filter(
            event_type=Event.EventType.DEADLINE,
            subject__sections__id__in=section_ids,
            start_datetime__gte=now,
        )
        .distinct()
        .order_by("start_datetime")[:5]
    )

    context = {
        "active_nav": "dashboard",
        "profile": profile,
        "gpa": compute_gpa(user),
        "todays_sections": todays_sections,
        "attendance_pct": attendance_pct,
        "subject_count": len({e.section.subject_id for e in enrollments}),
        "assignments_due": assignments_due,
        "assignments_due_count": Event.objects.filter(
            event_type=Event.EventType.DEADLINE, subject__sections__id__in=section_ids, start_datetime__gte=now
        ).distinct().count(),
        "upcoming_today_count": upcoming_today_count,
        "announcements": _announcements_for(user),
    }
    return render(request, "accounts/dashboard_student.html", context)


def teacher_dashboard(request):
    user = request.user
    now = timezone.localtime()
    today = now.date()
    weekday = today.weekday()

    sections = list(ClassSection.objects.filter(teacher=user).select_related("subject", "room__building"))
    todays_sections = sorted((s for s in sections if s.weekday == weekday), key=lambda s: s.start_time)

    cancelled_today = set(
        Event.objects.filter(
            event_type=Event.EventType.CLASS_CANCELLED,
            section__in=todays_sections,
            occurrence_date=today,
        ).values_list("section_id", flat=True)
    )
    for s in todays_sections:
        s.is_cancelled_today = s.id in cancelled_today
        s.active_session = AttendanceSession.objects.filter(section=s, date=today, is_active=True).first()
        s.student_count = Enrollment.objects.filter(section=s).count()

    context = {
        "active_nav": "dashboard",
        "todays_sections": todays_sections,
        "total_sections": len(sections),
        "total_students": Enrollment.objects.filter(section__teacher=user).values("student").distinct().count(),
        "announcements": Announcement.objects.all()[:5],
    }
    return render(request, "accounts/dashboard_teacher.html", context)


def admin_dashboard(request):
    today = timezone.localdate()
    context = {
        "active_nav": "dashboard",
        "total_students": User.objects.filter(role=User.Role.STUDENT).count(),
        "total_teachers": User.objects.filter(role=User.Role.TEACHER).count(),
        "total_subjects": Subject.objects.count(),
        "total_sections": ClassSection.objects.count(),
        "todays_events": Event.objects.filter(start_datetime__date=today).order_by("start_datetime"),
        "announcements": Announcement.objects.all()[:5],
    }
    return render(request, "accounts/dashboard_admin.html", context)


@login_required
def profile_view(request):
    user = request.user
    context = {"active_nav": "profile"}

    if user.is_student:
        profile = user.student_profile
        enrollments = list(Enrollment.objects.filter(student=user).select_related("section__subject"))
        section_ids = [e.section_id for e in enrollments]
        total_sessions = AttendanceSession.objects.filter(section_id__in=section_ids).count()
        present_count = AttendanceRecord.objects.filter(student=user, session__section_id__in=section_ids).count()
        subjects = list({e.section.subject.id: e.section.subject for e in enrollments}.values())
        context.update({
            "profile": profile,
            "gpa": compute_gpa(user),
            "subjects": subjects,
            "attendance_pct": round(present_count / total_sessions * 100) if total_sessions else None,
            "achievements": profile.achievements.all(),
        })
    elif user.is_teacher:
        context["teacher_profile"] = user.teacher_profile
        context["sections"] = ClassSection.objects.filter(teacher=user).select_related("subject")

    return render(request, "accounts/profile.html", context)


@login_required
def student_id_card_view(request):
    user = request.user
    if not user.is_student:
        return redirect("accounts:dashboard_redirect")

    profile = user.student_profile
    today = date.today()
    valid_until = date(today.year + 1, 6, 30) if today.month > 6 else date(today.year, 6, 30)
    serial_number = f"NUM-{profile.enrolled_on.year}-{user.id:06d}"

    qr_payload = {
        "student_id": profile.student_id,
        "name": user.get_full_name(),
        "email": user.email,
        "major": profile.major,
        "profile_url": request.build_absolute_uri(reverse("accounts:profile")),
    }

    context = {
        "active_nav": "student_id",
        "profile": profile,
        "valid_until": valid_until,
        "serial_number": serial_number,
        "qr_image": generate_qr_data_uri(json.dumps(qr_payload)),
    }
    return render(request, "accounts/student_id_card.html", context)
