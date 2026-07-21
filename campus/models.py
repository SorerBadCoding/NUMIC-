from django.db import models


class Building(models.Model):
    class Category(models.TextChoices):
        ENTRANCE = "entrance", "Main Entrance"
        ACADEMIC = "academic", "Academic Building"
        LIBRARY = "library", "Library"
        CAFETERIA = "cafeteria", "Cafeteria"
        STUDENT_SERVICES = "student_services", "Student Services"
        PARKING = "parking", "Parking"
        AUDITORIUM = "auditorium", "Auditorium"

    ICONS = {
        Category.ENTRANCE: "🚪",
        Category.ACADEMIC: "🏛️",
        Category.LIBRARY: "📚",
        Category.CAFETERIA: "🍜",
        Category.STUDENT_SERVICES: "🛎️",
        Category.PARKING: "🅿️",
        Category.AUDITORIUM: "🎓",
    }

    name = models.CharField(max_length=120)
    code = models.CharField(max_length=10, unique=True, help_text="Short building code, e.g. 'A'")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.ACADEMIC)
    latitude = models.FloatField()
    longitude = models.FloatField()
    departments = models.CharField(max_length=255, blank=True, help_text="Comma-separated departments housed here")
    opening_hours = models.CharField(max_length=120, default="Mon–Fri, 07:00–18:00")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"

    @property
    def icon(self):
        return self.ICONS.get(self.category, "📍")

    @property
    def department_list(self):
        return [d.strip() for d in self.departments.split(",") if d.strip()]


class Room(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="rooms")
    code = models.CharField(max_length=20, help_text="e.g. 'A305'")
    capacity = models.PositiveIntegerField(default=40)

    class Meta:
        ordering = ["building__code", "code"]
        unique_together = ("building", "code")

    def __str__(self):
        return self.code
