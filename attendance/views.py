from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from academics.models import ClassSection, Enrollment
from accounts.decorators import teacher_required
from notifications.models import Notification

from .models import AttendanceAttempt, AttendanceRecord, AttendanceSession, QRToken
from .qr import generate_qr_data_uri
from .utils import haversine_distance_meters

SIGNER = TimestampSigner()


@login_required
def attendance_home(request):
    user = request.user
    today = timezone.localdate()
    weekday = today.weekday()

    if user.is_student:
        enrollments = (
            Enrollment.objects.filter(student=user)
            .select_related("section__subject", "section__teacher", "section__room__building")
        )
        todays = sorted((e.section for e in enrollments if e.section.weekday == weekday), key=lambda s: s.start_time)
        rows = []
        for s in todays:
            session = AttendanceSession.objects.filter(section=s, date=today).first()
            marked = bool(session) and AttendanceRecord.objects.filter(session=session, student=user).exists()
            rows.append({"section": s, "session": session, "marked": marked})
        recent = (
            AttendanceRecord.objects.filter(student=user)
            .select_related("session__section__subject")
            .order_by("-marked_at")[:8]
        )
        return render(request, "attendance/home_student.html", {"active_nav": "attendance", "rows": rows, "recent": recent})

    if user.is_teacher:
        sections = ClassSection.objects.filter(teacher=user).select_related("subject", "room__building")
        todays = sorted((s for s in sections if s.weekday == weekday), key=lambda s: s.start_time)
        for s in todays:
            s.session = AttendanceSession.objects.filter(section=s, date=today).first()
            s.present_count = AttendanceRecord.objects.filter(session=s.session).count() if s.session else 0
            s.enrolled_count = Enrollment.objects.filter(section=s).count()
        return render(request, "attendance/home_teacher.html", {"active_nav": "attendance", "todays_sections": todays})

    active_sessions = (
        AttendanceSession.objects.filter(is_active=True)
        .select_related("section__subject", "section__teacher")
    )
    return render(request, "attendance/home_admin.html", {"active_nav": "attendance", "active_sessions": active_sessions})


@teacher_required
def teacher_session(request, section_id):
    section = get_object_or_404(ClassSection, id=section_id, teacher=request.user)
    today = timezone.localdate()
    if section.weekday != today.weekday():
        messages.error(request, "This class isn't scheduled for today.")
        return redirect("attendance:home")

    session, _ = AttendanceSession.objects.get_or_create(
        section=section, date=today, defaults={"opened_by": request.user}
    )
    if not session.is_active:
        session.is_active = True
        session.closed_at = None
        session.save(update_fields=["is_active", "closed_at"])

    context = {
        "active_nav": "attendance",
        "section": section,
        "session": session,
        "ttl": settings.ATTENDANCE_QR_TTL_SECONDS,
        "enrolled_count": Enrollment.objects.filter(section=section).count(),
    }
    return render(request, "attendance/teacher_session.html", context)


def _can_manage_session(user, session):
    return user.is_admin_role or session.section.teacher_id == user.id


@login_required
def qr_json(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    if not _can_manage_session(request.user, session):
        return HttpResponseForbidden()
    if not session.is_active:
        return JsonResponse({"active": False})

    now = timezone.now()
    token = session.tokens.filter(is_consumed=False, expires_at__gt=now).order_by("-created_at").first()
    if not token:
        token = QRToken.objects.create(
            session=session, expires_at=now + timedelta(seconds=settings.ATTENDANCE_QR_TTL_SECONDS)
        )

    payload = SIGNER.sign(f"{session.id}:{token.token}")
    image = generate_qr_data_uri(payload)
    seconds_left = max(0, int((token.expires_at - now).total_seconds()))
    return JsonResponse({"active": True, "image": image, "expires_in": seconds_left, "ttl": settings.ATTENDANCE_QR_TTL_SECONDS})


@login_required
def roster_json(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    if not _can_manage_session(request.user, session):
        return HttpResponseForbidden()

    records = session.records.select_related("student__student_profile").order_by("-marked_at")
    data = [
        {
            "name": r.student.get_full_name(),
            "student_id": getattr(r.student.student_profile, "student_id", ""),
            "time": timezone.localtime(r.marked_at).strftime("%H:%M:%S"),
            "distance": round(r.distance_meters),
        }
        for r in records
    ]
    return JsonResponse({"count": len(data), "records": data, "active": session.is_active})


@login_required
@require_POST
def close_session(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    if not _can_manage_session(request.user, session):
        return HttpResponseForbidden()
    session.close()
    return JsonResponse({"ok": True})


@login_required
def scan_view(request):
    if not request.user.is_student:
        return redirect("attendance:home")
    context = {
        "active_nav": "attendance",
        "campus_lat": settings.CAMPUS_LATITUDE,
        "campus_lng": settings.CAMPUS_LONGITUDE,
        "radius": settings.CAMPUS_ATTENDANCE_RADIUS_METERS,
    }
    return render(request, "attendance/scan.html", context)


@login_required
@require_POST
def submit_attendance(request):
    user = request.user
    if not user.is_student:
        return JsonResponse({"ok": False, "message": "Only students can submit attendance."}, status=403)

    payload = request.POST.get("payload", "")
    lat = request.POST.get("lat")
    lng = request.POST.get("lng")
    device_ts = request.POST.get("device_timestamp")

    def log_attempt(result, detail="", session=None):
        AttendanceAttempt.objects.create(
            student=user, session=session, result=result, detail=detail,
            latitude=float(lat) if lat else None, longitude=float(lng) if lng else None,
        )

    try:
        unsigned = SIGNER.unsign(payload, max_age=settings.ATTENDANCE_QR_TTL_SECONDS + 15)
    except SignatureExpired:
        log_attempt(AttendanceAttempt.Result.EXPIRED_TOKEN)
        return JsonResponse({"ok": False, "reason": "expired_token", "message": "This QR code has expired. Ask your teacher for a fresh one."})
    except BadSignature:
        log_attempt(AttendanceAttempt.Result.INVALID_TOKEN)
        return JsonResponse({"ok": False, "reason": "invalid_token", "message": "Invalid or tampered QR code."})

    try:
        session_id_str, token_str = unsigned.split(":", 1)
        session_id = int(session_id_str)
    except ValueError:
        log_attempt(AttendanceAttempt.Result.INVALID_TOKEN)
        return JsonResponse({"ok": False, "reason": "invalid_token", "message": "Invalid QR code."})

    token = (
        QRToken.objects.filter(token=token_str, session_id=session_id)
        .select_related("session__section__subject")
        .first()
    )
    if not token:
        log_attempt(AttendanceAttempt.Result.INVALID_TOKEN)
        return JsonResponse({"ok": False, "reason": "invalid_token", "message": "Invalid QR code."})

    session = token.session

    if token.is_consumed:
        log_attempt(AttendanceAttempt.Result.ALREADY_CONSUMED, session=session)
        return JsonResponse({"ok": False, "reason": "already_consumed", "message": "This QR code was already used. Ask your teacher for a fresh one."})

    if token.is_expired:
        log_attempt(AttendanceAttempt.Result.EXPIRED_TOKEN, session=session)
        return JsonResponse({"ok": False, "reason": "expired_token", "message": "This QR code has expired."})

    if not session.is_active:
        log_attempt(AttendanceAttempt.Result.SESSION_CLOSED, session=session)
        return JsonResponse({"ok": False, "reason": "session_closed", "message": "Attendance is closed for this class."})

    if not Enrollment.objects.filter(student=user, section=session.section).exists():
        log_attempt(AttendanceAttempt.Result.NOT_ENROLLED, session=session)
        return JsonResponse({"ok": False, "reason": "not_enrolled", "message": "You're not enrolled in this subject."})

    now = timezone.localtime()
    class_start = timezone.make_aware(datetime.combine(session.date, session.section.start_time))
    class_end = timezone.make_aware(datetime.combine(session.date, session.section.end_time))
    window_start = class_start - timedelta(minutes=settings.ATTENDANCE_GRACE_MINUTES_BEFORE)
    window_end = class_end + timedelta(minutes=settings.ATTENDANCE_GRACE_MINUTES_AFTER)
    if not (window_start <= now <= window_end):
        log_attempt(AttendanceAttempt.Result.OUTSIDE_TIME_WINDOW, session=session)
        return JsonResponse({"ok": False, "reason": "outside_time_window", "message": "Attendance is only accepted during class time."})

    if AttendanceRecord.objects.filter(session=session, student=user).exists():
        log_attempt(AttendanceAttempt.Result.ALREADY_MARKED, session=session)
        return JsonResponse({"ok": False, "reason": "already_marked", "message": "You've already been marked present for this class."})

    if lat is None or lng is None:
        log_attempt(AttendanceAttempt.Result.OUT_OF_RANGE, session=session, detail="no gps")
        return JsonResponse({"ok": False, "reason": "out_of_range", "message": "Location access is required to mark attendance."})

    lat_f, lng_f = float(lat), float(lng)
    distance = haversine_distance_meters(lat_f, lng_f, settings.CAMPUS_LATITUDE, settings.CAMPUS_LONGITUDE)
    if distance > settings.CAMPUS_ATTENDANCE_RADIUS_METERS:
        log_attempt(AttendanceAttempt.Result.OUT_OF_RANGE, session=session, detail=f"{distance:.0f}m from campus")
        return JsonResponse({
            "ok": False, "reason": "out_of_range",
            "message": f"You're about {int(distance)}m from campus — attendance is only accepted within {settings.CAMPUS_ATTENDANCE_RADIUS_METERS}m.",
        })

    device_dt = parse_datetime(device_ts) if device_ts else None
    if device_dt and abs((timezone.now() - device_dt).total_seconds()) > 300:
        log_attempt(AttendanceAttempt.Result.INVALID_TOKEN, session=session, detail="device clock mismatch")
        return JsonResponse({"ok": False, "reason": "invalid_token", "message": "Your device clock looks incorrect. Please sync it and try again."})

    record = AttendanceRecord.objects.create(
        session=session, student=user, token=token,
        latitude=lat_f, longitude=lng_f, distance_meters=distance, device_timestamp=device_dt,
    )
    token.is_consumed = True
    token.consumed_by = user
    token.consumed_at = timezone.now()
    token.save(update_fields=["is_consumed", "consumed_by", "consumed_at"])

    log_attempt(AttendanceAttempt.Result.SUCCESS, session=session)

    Notification.objects.create(
        user=user, notif_type=Notification.NotifType.ATTENDANCE,
        title="Attendance Recorded",
        body=f"{session.section.subject.name} — {record.distance_meters:.0f}m from campus center.",
    )

    return JsonResponse({"ok": True, "message": f"Attendance recorded for {session.section.subject.name}."})
