from django.db import migrations

# Real coordinates for National University of Management — Veal Sbov campus,
# replacing the placeholder seed-data coordinates used before the campus
# location was confirmed.
COORDS_BY_CATEGORY = {
    "entrance": (11.521980, 104.965870, "Main Entrance", "MAIN"),
    "library": (11.522560, 104.965900, "NUM Central Library", "LIB"),
    "cafeteria": (11.522230, 104.966360, "Student Cafeteria", "CAF"),
    "auditorium": (11.523060, 104.965820, "NUM Auditorium", "AUD"),
    "student_services": (11.522330, 104.965540, "Student Services Center", "SVC"),
    "parking": (11.521920, 104.965300, "Parking Area", "PK"),
}

# "academic" buildings aren't unique by category (there are two), so they're
# disambiguated by a department keyword instead.
ACADEMIC_IT = dict(
    latitude=11.522870, longitude=104.966400,
    name="Building A — Information Technology", code="A",
    departments="Department of Information Technology, Department of Computer Science",
)
ACADEMIC_MGMT = dict(
    latitude=11.522880, longitude=104.965300,
    name="Building B — Management & Business", code="B",
    departments="Department of Management, Department of Finance and Banking",
)
IT_KEYWORDS = ("information technology", "computer science")
MGMT_KEYWORDS = ("management", "finance")


def update_coordinates(apps, schema_editor):
    Building = apps.get_model("campus", "Building")

    for category, (lat, lng, default_name, default_code) in COORDS_BY_CATEGORY.items():
        rows = list(Building.objects.filter(category=category))
        if rows:
            for building in rows:
                building.latitude = lat
                building.longitude = lng
                building.save(update_fields=["latitude", "longitude"])
        elif not Building.objects.filter(code=default_code).exists():
            Building.objects.create(
                name=default_name, code=default_code, category=category,
                latitude=lat, longitude=lng,
            )

    matched_it = matched_mgmt = False
    for building in Building.objects.filter(category="academic"):
        departments = (building.departments or "").lower()
        if any(keyword in departments for keyword in IT_KEYWORDS):
            building.latitude = ACADEMIC_IT["latitude"]
            building.longitude = ACADEMIC_IT["longitude"]
            building.save(update_fields=["latitude", "longitude"])
            matched_it = True
        elif any(keyword in departments for keyword in MGMT_KEYWORDS):
            building.latitude = ACADEMIC_MGMT["latitude"]
            building.longitude = ACADEMIC_MGMT["longitude"]
            building.save(update_fields=["latitude", "longitude"])
            matched_mgmt = True

    if not matched_it and not Building.objects.filter(code=ACADEMIC_IT["code"]).exists():
        Building.objects.create(category="academic", **ACADEMIC_IT)
    if not matched_mgmt and not Building.objects.filter(code=ACADEMIC_MGMT["code"]).exists():
        Building.objects.create(category="academic", **ACADEMIC_MGMT)


def noop_reverse(apps, schema_editor):
    # Coordinates-only correction — nothing meaningful to revert to.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("campus", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(update_coordinates, noop_reverse),
    ]
