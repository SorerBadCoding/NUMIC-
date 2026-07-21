from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from academics.models import ClassSection, Subject
from accounts.decorators import admin_required
from campus.models import Room
from notifications.models import Notification
from notifications.services import notify_all_students, notify_section_students

from .models import Event
from .services import calendar_events


@login_required
def calendar_view(request):
    context = {
        "active_nav": "calendar",
        "is_admin": request.user.is_admin_role,
        "event_types": Event.EventType.choices,
        "subjects": Subject.objects.all(),
        "sections": ClassSection.objects.select_related("subject", "teacher").all(),
        "rooms": Room.objects.select_related("building").all(),
        "teachers": ClassSection.objects.select_related("teacher").values_list("teacher__id", "teacher__first_name", "teacher__last_name").distinct(),
    }
    return render(request, "calendar_app/view.html", context)


@login_required
def events_json(request):
    start_raw = request.GET.get("start", "")
    end_raw = request.GET.get("end", "")
    try:
        start_date = date.fromisoformat(start_raw[:10])
        end_date = date.fromisoformat(end_raw[:10])
    except ValueError:
        return JsonResponse([], safe=False)

    events = calendar_events(request.user, start_date, end_date)
    return JsonResponse(events, safe=False)


@admin_required
@require_POST
def event_create(request):
    event_type = request.POST.get("event_type")
    title = request.POST.get("title", "").strip()
    start_dt = parse_datetime(request.POST.get("start_datetime", ""))
    end_dt = parse_datetime(request.POST.get("end_datetime", ""))
    if not (title and event_type and start_dt and end_dt):
        return JsonResponse({"error": "Missing required fields."}, status=400)

    subject_id = request.POST.get("subject") or None
    room_id = request.POST.get("room") or None

    event = Event.objects.create(
        title=title,
        event_type=event_type,
        description=request.POST.get("description", ""),
        start_datetime=start_dt,
        end_datetime=end_dt,
        subject_id=subject_id,
        room_id=room_id,
        created_by=request.user,
    )

    if event.event_type in (Event.EventType.HOLIDAY, Event.EventType.UNIVERSITY_EVENT):
        notify_all_students(
            Notification.NotifType.SCHEDULE_UPDATED if event.event_type == Event.EventType.HOLIDAY else Notification.NotifType.ANNOUNCEMENT,
            f"{event.get_event_type_display()}: {event.title}",
            event.start_datetime.strftime("%A, %b %d"),
        )
    elif event.subject_id and event.event_type in (Event.EventType.MIDTERM, Event.EventType.FINAL, Event.EventType.DEADLINE):
        for section in ClassSection.objects.filter(subject_id=event.subject_id):
            notify_section_students(
                section,
                Notification.NotifType.EXAM_REMINDER if event.event_type in (Event.EventType.MIDTERM, Event.EventType.FINAL) else Notification.NotifType.DEADLINE_REMINDER,
                f"{event.get_event_type_display()}: {event.title}",
                f"{event.subject.code} — {event.start_datetime.strftime('%A, %b %d, %H:%M')}",
            )

    return JsonResponse({"ok": True, "id": event.id})


@admin_required
@require_POST
def event_delete(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return JsonResponse({"ok": True})


@admin_required
@require_POST
def cancel_occurrence(request):
    section_id = request.POST.get("section_id")
    occurrence_date = date.fromisoformat(request.POST.get("date"))
    reason = request.POST.get("reason", "No Class Today")
    section = get_object_or_404(ClassSection, id=section_id)

    start_dt = timezone.make_aware(datetime.combine(occurrence_date, section.start_time))
    end_dt = timezone.make_aware(datetime.combine(occurrence_date, section.end_time))

    event, created = Event.objects.get_or_create(
        event_type=Event.EventType.CLASS_CANCELLED,
        section=section,
        occurrence_date=occurrence_date,
        defaults={
            "title": f"{section.subject.code} cancelled",
            "description": reason,
            "start_datetime": start_dt,
            "end_datetime": end_dt,
            "subject": section.subject,
            "created_by": request.user,
        },
    )
    if not created:
        event.description = reason
        event.save(update_fields=["description"])

    notify_section_students(
        section, Notification.NotifType.CLASS_CANCELLED,
        f"Class Cancelled: {section.subject.name}",
        f"{reason} — {occurrence_date}",
    )
    return JsonResponse({"ok": True})


@admin_required
@require_POST
def restore_occurrence(request):
    section_id = request.POST.get("section_id")
    occurrence_date = request.POST.get("date")
    Event.objects.filter(
        event_type=Event.EventType.CLASS_CANCELLED, section_id=section_id, occurrence_date=occurrence_date
    ).delete()
    return JsonResponse({"ok": True})


@admin_required
@require_POST
def change_room(request):
    section_id = request.POST.get("section_id")
    room_id = request.POST.get("room_id") or None
    section = get_object_or_404(ClassSection, id=section_id)
    section.room_id = room_id
    section.save(update_fields=["room"])

    notify_section_students(
        section, Notification.NotifType.SCHEDULE_UPDATED,
        f"Classroom Changed: {section.subject.name}",
        f"Now in {section.room}" if section.room else "Room to be announced",
    )
    return JsonResponse({"ok": True})


@admin_required
@require_POST
def section_create(request):
    section = ClassSection.objects.create(
        subject_id=request.POST.get("subject"),
        teacher_id=request.POST.get("teacher") or None,
        room_id=request.POST.get("room") or None,
        year=request.POST.get("year", 1),
        semester=request.POST.get("semester", 1),
        weekday=request.POST.get("weekday"),
        start_time=request.POST.get("start_time"),
        end_time=request.POST.get("end_time"),
        academic_term=request.POST.get("academic_term", "Spring 2026"),
    )
    return JsonResponse({"ok": True, "id": section.id})
