from django.db import models


class Grade(models.Model):
    """Scores for one student's enrollment in one class section.

    Weighting: assignments 20%, midterm 30%, final 50% — a typical NUM
    breakdown. All component scores are out of 100.
    """

    ASSIGNMENT_WEIGHT = 0.2
    MIDTERM_WEIGHT = 0.3
    FINAL_WEIGHT = 0.5

    GRADE_SCALE = [
        (90, "A", 4.0), (85, "A-", 3.7),
        (80, "B+", 3.3), (75, "B", 3.0), (70, "B-", 2.7),
        (65, "C+", 2.3), (60, "C", 2.0), (55, "C-", 1.7),
        (50, "D", 1.0), (0, "F", 0.0),
    ]

    enrollment = models.OneToOneField("academics.Enrollment", on_delete=models.CASCADE, related_name="grade")
    assignment_score = models.FloatField(null=True, blank=True)
    midterm_score = models.FloatField(null=True, blank=True)
    final_score = models.FloatField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.enrollment} — {self.letter_grade}"

    @property
    def has_final(self):
        return self.final_score is not None

    @property
    def total_score(self):
        parts = []
        if self.assignment_score is not None:
            parts.append(self.assignment_score * self.ASSIGNMENT_WEIGHT)
        if self.midterm_score is not None:
            parts.append(self.midterm_score * self.MIDTERM_WEIGHT)
        if self.final_score is not None:
            parts.append(self.final_score * self.FINAL_WEIGHT)
        weight_used = (
            (self.ASSIGNMENT_WEIGHT if self.assignment_score is not None else 0)
            + (self.MIDTERM_WEIGHT if self.midterm_score is not None else 0)
            + (self.FINAL_WEIGHT if self.final_score is not None else 0)
        )
        if not weight_used:
            return None
        return round(sum(parts) / weight_used, 1)

    def _scale_lookup(self):
        score = self.total_score
        if score is None:
            return None
        for threshold, letter, points in self.GRADE_SCALE:
            if score >= threshold:
                return letter, points
        return "F", 0.0

    @property
    def letter_grade(self):
        result = self._scale_lookup()
        return result[0] if result else "—"

    @property
    def gpa_points(self):
        result = self._scale_lookup()
        return result[1] if result else None


def compute_gpa(student_user):
    """Credit-weighted GPA across all of a student's graded enrollments."""
    from academics.models import Enrollment

    enrollments = (
        Enrollment.objects.filter(student=student_user)
        .select_related("section__subject", "grade")
    )
    total_points, total_credits = 0.0, 0
    for enrollment in enrollments:
        grade = getattr(enrollment, "grade", None)
        if grade and grade.gpa_points is not None:
            credits = enrollment.section.subject.credits
            total_points += grade.gpa_points * credits
            total_credits += credits
    if not total_credits:
        return None
    return round(total_points / total_credits, 2)
