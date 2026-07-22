from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from academics.models import ClassSection, Enrollment
from accounts.decorators import teacher_required

from .models import Grade, compute_gpa


@login_required
def grades_view(request):
    user = request.user
    if not user.is_student:
        return redirect("accounts:dashboard_redirect")

    enrollments = (
        Enrollment.objects.filter(student=user)
        .select_related("section__subject", "grade")
        .order_by("section__subject__code")
    )
    rows = [{"subject": e.section.subject, "grade": getattr(e, "grade", None)} for e in enrollments]

    context = {
        "active_nav": "grades",
        "rows": rows,
        "gpa": compute_gpa(user),
    }
    return render(request, "grades/index.html", context)


def _can_manage_gradebook(user, section):
    """Only the section's own teacher, or an admin, may view/edit its gradebook."""
    return user.is_admin_role or (user.is_teacher and section.teacher_id == user.id)


@teacher_required
def teacher_classes_view(request):
    sections = (
        ClassSection.objects.filter(teacher=request.user)
        .select_related("subject", "room__building")
        .annotate(enrolled_count=Count("enrollments"))
        .order_by("weekday", "start_time")
    )
    context = {"active_nav": "teacher_classes", "sections": sections}
    return render(request, "grades/teacher_classes.html", context)


@login_required
def gradebook_view(request, section_id):
    section = get_object_or_404(
        ClassSection.objects.select_related("subject", "teacher", "room__building"), id=section_id
    )
    if not _can_manage_gradebook(request.user, section):
        return HttpResponseForbidden("You do not have permission to view this gradebook.")

    enrollments = (
        Enrollment.objects.filter(section=section)
        .select_related("student__student_profile", "grade")
        .order_by("student__last_name", "student__first_name")
    )
    rows = []
    for enrollment in enrollments:
        grade = getattr(enrollment, "grade", None)
        rows.append({
            "enrollment": enrollment,
            "student": enrollment.student,
            "assignment_score": grade.assignment_score if grade else None,
            "midterm_score": grade.midterm_score if grade else None,
            "final_score": grade.final_score if grade else None,
            "total_score": grade.total_score if grade else None,
            "letter_grade": grade.letter_grade if grade else "—",
            "gpa_points": grade.gpa_points if grade else None,
        })

    context = {
        "active_nav": "teacher_classes",
        "section": section,
        "rows": rows,
    }
    return render(request, "grades/gradebook.html", context)


def _parse_score(raw):
    """Returns (value, error). Blank is valid (clears the score)."""
    raw = (raw or "").strip()
    if raw == "":
        return None, None
    try:
        value = float(raw)
    except ValueError:
        return None, "Enter a number between 0 and 100."
    if value < 0 or value > 100:
        return None, "Enter a number between 0 and 100."
    return value, None


@login_required
@require_POST
def gradebook_save(request, section_id):
    section = get_object_or_404(ClassSection, id=section_id)
    if not _can_manage_gradebook(request.user, section):
        return HttpResponseForbidden("You do not have permission to edit this gradebook.")

    enrollment = get_object_or_404(Enrollment, id=request.POST.get("enrollment_id"), section=section)

    errors = {}
    values = {}
    for field in ("assignment_score", "midterm_score", "final_score"):
        value, error = _parse_score(request.POST.get(field))
        if error:
            errors[field] = error
        else:
            values[field] = value

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    grade, _created = Grade.objects.get_or_create(enrollment=enrollment)
    grade.assignment_score = values["assignment_score"]
    grade.midterm_score = values["midterm_score"]
    grade.final_score = values["final_score"]
    grade.save()

    return JsonResponse({
        "ok": True,
        "total_score": grade.total_score,
        "letter_grade": grade.letter_grade,
        "gpa_points": grade.gpa_points,
    })
