from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from attendance.models import AttendanceRecord, AttendanceSession
from calendar_app.models import Event
from grades.models import Grade
from notifications.models import Announcement

from .models import ClassSection, Enrollment, Material, Subject


@login_required
def subject_list(request):
    user = request.user
    items = []

    if user.is_student:
        enrollments = (
            Enrollment.objects.filter(student=user)
            .select_related("section__subject", "section__teacher", "section__room__building")
        )
        seen = set()
        for e in enrollments:
            if e.section.subject_id in seen:
                continue
            seen.add(e.section.subject_id)
            items.append({"subject": e.section.subject, "section": e.section})
    elif user.is_teacher:
        sections = ClassSection.objects.filter(teacher=user).select_related("subject", "room__building")
        items = [{"subject": s.subject, "section": s} for s in sections]
    else:
        sections = ClassSection.objects.select_related("subject", "teacher", "room__building")
        items = [{"subject": s.subject, "section": s} for s in sections]

    return render(request, "academics/subject_list.html", {"active_nav": "subjects", "items": items})


@login_required
def subject_detail(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    user = request.user
    tab = request.GET.get("tab", "materials")

    section = None
    if user.is_student:
        enrollment = (
            Enrollment.objects.filter(student=user, section__subject=subject)
            .select_related("section__teacher", "section__room__building")
            .first()
        )
        section = enrollment.section if enrollment else None
    elif user.is_teacher:
        section = ClassSection.objects.filter(subject=subject, teacher=user).select_related("room__building").first()
    else:
        section = ClassSection.objects.filter(subject=subject).select_related("teacher", "room__building").first()

    context = {
        "active_nav": "subjects",
        "subject": subject,
        "section": section,
        "tab": tab,
        "materials": Material.objects.filter(section=section) if section else [],
        "deadlines": Event.objects.filter(event_type=Event.EventType.DEADLINE, subject=subject).order_by("start_datetime"),
        "announcements": Announcement.objects.filter(subject=subject),
        "now": timezone.now(),
    }

    if user.is_student and section:
        sessions = AttendanceSession.objects.filter(section=section).order_by("-date")
        present_ids = set(
            AttendanceRecord.objects.filter(student=user, session__section=section).values_list("session_id", flat=True)
        )
        context["attendance_history"] = [
            {"session": sess, "present": sess.id in present_ids} for sess in sessions
        ]
        context["grade"] = Grade.objects.filter(enrollment__student=user, enrollment__section=section).first()

    return render(request, "academics/subject_detail.html", context)
