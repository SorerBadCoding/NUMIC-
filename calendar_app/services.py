from datetime import datetime, timedelta

from django.db.models import Q

from academics.models import ClassSection, Enrollment

from .models import Event


def _visible_sections(user):
    if user.is_student:
        section_ids = Enrollment.objects.filter(student=user).values_list("section_id", flat=True)
        return ClassSection.objects.filter(id__in=section_ids).select_related("subject", "teacher", "room__building")
    if user.is_teacher:
        return ClassSection.objects.filter(teacher=user).select_related("subject", "teacher", "room__building")
    return ClassSection.objects.select_related("subject", "teacher", "room__building")


def _visible_subject_ids(user):
    if user.is_student:
        return set(
            Enrollment.objects.filter(student=user).values_list("section__subject_id", flat=True)
        )
    if user.is_teacher:
        return set(ClassSection.objects.filter(teacher=user).values_list("subject_id", flat=True))
    return None  # admin sees all


def class_occurrences(user, start_date, end_date):
    sections = list(_visible_sections(user))
    overrides = {
        (e.section_id, e.occurrence_date): e
        for e in Event.objects.filter(
            event_type=Event.EventType.CLASS_CANCELLED,
            occurrence_date__range=(start_date, end_date),
        )
    }

    occurrences = []
    day = start_date
    while day <= end_date:
        weekday = day.weekday()
        for s in sections:
            if s.weekday != weekday:
                continue
            override = overrides.get((s.id, day))
            occurrences.append({
                "id": f"class-{s.id}-{day.isoformat()}",
                "title": ("🚫 " if override else "") + s.subject.name,
                "start": datetime.combine(day, s.start_time).isoformat(),
                "end": datetime.combine(day, s.end_time).isoformat(),
                "color": Event.COLORS[Event.EventType.CLASS_CANCELLED] if override else "#2f6fed",
                "kind": "class",
                "cancelled": bool(override),
                "cancel_reason": override.description if override else "",
                "section_id": s.id,
                "date": day.isoformat(),
                "subject_code": s.subject.code,
                "subject_name": s.subject.name,
                "teacher": s.teacher.get_full_name() if s.teacher else "TBA",
                "room": str(s.room) if s.room else "TBA",
                "building": s.room.building.name if s.room else "",
            })
        day += timedelta(days=1)
    return occurrences


def calendar_events(user, start_date, end_date):
    subject_ids = _visible_subject_ids(user)

    qs = Event.objects.exclude(event_type=Event.EventType.CLASS_CANCELLED).filter(
        start_datetime__date__lte=end_date, end_datetime__date__gte=start_date
    )
    if subject_ids is not None:
        qs = qs.filter(
            Q(event_type__in=[Event.EventType.HOLIDAY, Event.EventType.UNIVERSITY_EVENT])
            | Q(subject_id__in=subject_ids)
        )

    events = [
        {
            "id": f"event-{e.id}",
            "db_id": e.id,
            "title": e.title,
            "start": e.start_datetime.isoformat(),
            "end": e.end_datetime.isoformat(),
            "color": e.color,
            "kind": "event",
            "event_type": e.event_type,
            "event_type_label": e.get_event_type_display(),
            "description": e.description,
            "subject_code": e.subject.code if e.subject else "",
            "all_day": e.is_all_day,
        }
        for e in qs
    ]

    return class_occurrences(user, start_date, end_date) + events
