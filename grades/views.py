from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from academics.models import Enrollment

from .models import compute_gpa


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
