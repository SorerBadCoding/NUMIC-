import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from academics.models import ClassSection, Enrollment, Material, Subject
from accounts.models import Achievement, StudentProfile, TeacherProfile, User
from attendance.models import AttendanceAttempt, AttendanceRecord, AttendanceSession
from attendance.utils import haversine_distance_meters
from calendar_app.models import Event
from campus.models import Building, Room
from django.conf import settings
from grades.models import Grade
from notifications.models import Announcement, Notification

PASSWORD = "num12345"

TEACHERS = [
    dict(username="teacher1", first="Kim", last="Vichet", title="Senior Lecturer", dept="Department of Information Technology"),
    dict(username="teacher2", first="Chea", last="Sreymom", title="Lecturer", dept="Department of Information Technology"),
    dict(username="teacher3", first="Prak", last="Rithy", title="Lecturer", dept="Department of Information Technology"),
    dict(username="teacher4", first="Meas", last="Chanthou", title="Senior Lecturer", dept="Department of Management"),
]

STUDENT_NAMES = [
    ("Potling", ""),
    ("Sok", "Dara"), ("Heng", "Bopha"), ("Chan", "Sopheak"), ("Prak", "Panha"),
    ("Long", "Chansocheata"), ("Pich", "Rathanak"), ("Vann", "Sreynich"),
    ("Sun", "Kunthea"), ("Ly", "Vuthy"), ("Sao", "Malis"), ("Chhun", "Ratana"),
    ("Ros", "Sovannaphumi"), ("Keo", "Leakena"),
]

BUILDINGS = [
    dict(code="MAIN", name="Main Entrance", category=Building.Category.ENTRANCE, dx=0, dy=-0.0012,
         departments="", hours="Open 24 hours", desc="Main gate of NUM Veal Sbov Campus."),
    dict(code="A", name="Building A — Information Technology", category=Building.Category.ACADEMIC, dx=0.0008, dy=0.0006,
         departments="Department of Information Technology, Department of Computer Science",
         hours="Mon–Sat, 07:00–18:00", desc="Lecture halls and computer labs for IT programs."),
    dict(code="B", name="Building B — Management & Business", category=Building.Category.ACADEMIC, dx=-0.0009, dy=0.0007,
         departments="Department of Management, Department of Finance and Banking",
         hours="Mon–Sat, 07:00–18:00", desc="Lecture halls for Management and Business programs."),
    dict(code="LIB", name="NUM Central Library", category=Building.Category.LIBRARY, dx=0.0004, dy=-0.0004,
         departments="", hours="Mon–Sat, 07:00–20:00", desc="Books, study rooms, and digital resources."),
    dict(code="CAF", name="Student Cafeteria", category=Building.Category.CAFETERIA, dx=-0.0005, dy=-0.0006,
         departments="", hours="Daily, 06:30–19:00", desc="Food court and coffee shop."),
    dict(code="SVC", name="Student Services Center", category=Building.Category.STUDENT_SERVICES, dx=0.0002, dy=0.0012,
         departments="Registrar, Scholarships Office, IT Helpdesk", hours="Mon–Fri, 08:00–17:00", desc="Registration, ID cards, and student support."),
    dict(code="PK", name="Parking Area", category=Building.Category.PARKING, dx=-0.0011, dy=0.0002,
         departments="", hours="Open 24 hours", desc="Student and staff parking."),
    dict(code="AUD", name="NUM Auditorium", category=Building.Category.AUDITORIUM, dx=0.0011, dy=-0.0009,
         departments="", hours="Event hours only", desc="Main hall for ceremonies and university events."),
]

SUBJECTS = [
    dict(code="CS101", name="Introduction to Programming", credits=4),
    dict(code="CS102", name="Data Structures and Algorithms", credits=4),
    dict(code="MATH201", name="Discrete Mathematics", credits=3),
    dict(code="CS201", name="Computer Architecture and Optimization", credits=3),
    dict(code="CS202", name="Introduction to Database Systems", credits=3),
    dict(code="CS203", name="Computer Networks", credits=3),
    dict(code="CS204", name="Web Development", credits=3),
    dict(code="ENG101", name="English for IT Professionals", credits=2),
    dict(code="MGT101", name="Principles of Management", credits=3),
]

# subject_code, teacher_username, room_code, weekday(0=Mon), start, end
SCHEDULE = [
    ("CS102", "teacher1", "A101", 0, "08:00", "10:00"),
    ("ENG101", "teacher4", "A104", 0, "13:00", "14:30"),
    ("CS101", "teacher3", "A103", 1, "08:00", "09:30"),
    ("MATH201", "teacher2", "A102", 1, "10:00", "12:00"),
    ("CS201", "teacher1", "A305", 2, "08:00", "10:00"),
    ("CS202", "teacher2", "A103", 3, "13:00", "15:00"),
    ("CS203", "teacher3", "B101", 4, "10:00", "12:00"),
    ("MGT101", "teacher4", "B103", 4, "15:00", "16:30"),
    ("CS204", "teacher3", "B102", 5, "08:00", "10:00"),
]


class Command(BaseCommand):
    help = "Seed the NUM Student Portal with realistic demo data."

    @transaction.atomic
    def handle(self, *args, **options):
        if User.objects.filter(username="student1").exists():
            self.stdout.write(self.style.WARNING("Seed data already present — skipping. Delete db.sqlite3 to reseed."))
            return

        today = timezone.localdate()

        # -- Buildings & rooms ------------------------------------------------
        # get_or_create (not create): campus.0002_update_campus_coordinates
        # creates these same building codes when run against an empty table,
        # and on a fresh database `migrate` always runs before `seed_data`
        # (see railway.json) — so a plain .create() here would collide with
        # the unique `code` constraint. Reusing the existing row also means
        # the migration's real campus coordinates win over this dict's
        # jittered placeholder offsets, which is the correct outcome anyway.
        buildings = {}
        for b in BUILDINGS:
            building, _ = Building.objects.get_or_create(
                code=b["code"],
                defaults=dict(
                    name=b["name"], category=b["category"],
                    latitude=settings.CAMPUS_LATITUDE + b["dy"], longitude=settings.CAMPUS_LONGITUDE + b["dx"],
                    departments=b["departments"], opening_hours=b["hours"], description=b["desc"],
                ),
            )
            buildings[b["code"]] = building

        rooms = {}
        for code in ["A101", "A102", "A103", "A104", "A305"]:
            rooms[code] = Room.objects.create(building=buildings["A"], code=code, capacity=45)
        for code in ["B101", "B102", "B103"]:
            rooms[code] = Room.objects.create(building=buildings["B"], code=code, capacity=45)
        self.stdout.write(self.style.SUCCESS(f"Created {len(buildings)} buildings, {len(rooms)} rooms."))

        # -- Users --------------------------------------------------------------
        admin = User.objects.create_user(
            username="admin1", password=PASSWORD, first_name="Heng", last_name="Sovann",
            email="admin1@num.edu.kh", role=User.Role.ADMIN, is_staff=True, is_superuser=True,
        )

        teachers = {}
        for t in TEACHERS:
            user = User.objects.create_user(
                username=t["username"], password=PASSWORD, first_name=t["first"], last_name=t["last"],
                email=f"{t['username']}@num.edu.kh", role=User.Role.TEACHER,
            )
            TeacherProfile.objects.create(user=user, staff_id=f"STF{1000 + len(teachers)}", department=t["dept"], title=t["title"])
            teachers[t["username"]] = user
        self.stdout.write(self.style.SUCCESS(f"Created admin + {len(teachers)} teachers."))

        students = []
        for i, (first, last) in enumerate(STUDENT_NAMES, start=1):
            username = f"student{i}"
            user = User.objects.create_user(
                username=username, password=PASSWORD, first_name=first, last_name=last,
                email=f"{username}@num.edu.kh", role=User.Role.STUDENT, phone=f"+855 9{i:02d} 000 {100 + i}",
            )
            StudentProfile.objects.create(
                user=user, student_id=f"NUM2026CS{i:04d}", major="Computer Science", year=1, semester=2,
            )
            students.append(user)
        self.stdout.write(self.style.SUCCESS(f"Created {len(students)} students."))

        # -- Subjects & sections --------------------------------------------
        subjects = {}
        for s in SUBJECTS:
            subjects[s["code"]] = Subject.objects.create(code=s["code"], name=s["name"], credits=s["credits"])

        sections = {}
        for subj_code, teacher_username, room_code, weekday, start, end in SCHEDULE:
            section = ClassSection.objects.create(
                subject=subjects[subj_code], teacher=teachers[teacher_username], room=rooms[room_code],
                year=1, semester=2, weekday=weekday,
                start_time=datetime.strptime(start, "%H:%M").time(),
                end_time=datetime.strptime(end, "%H:%M").time(),
                academic_term="Summer 2026",
            )
            sections[subj_code] = section
        self.stdout.write(self.style.SUCCESS(f"Created {len(sections)} class sections."))

        # -- Enrollments ------------------------------------------------------
        for student in students:
            for section in sections.values():
                Enrollment.objects.create(student=student, section=section)

        # -- Materials ----------------------------------------------------------
        Material.objects.create(section=sections["CS102"], title="Lecture 1 Slides — Arrays & Linked Lists",
                                 description="Introductory slide deck.", uploaded_by=teachers["teacher1"])
        Material.objects.create(section=sections["CS102"], title="Lab Sheet 2 — Stacks and Queues",
                                 description="Hands-on lab exercise.", uploaded_by=teachers["teacher1"])
        Material.objects.create(section=sections["CS202"], title="Database Design Cheat Sheet",
                                 description="ER diagrams and normalization quick reference.", uploaded_by=teachers["teacher2"])

        # -- Past attendance sessions & records --------------------------------
        present_count = 0
        for section in sections.values():
            for weeks_ago in range(4, 0, -1):
                occurrence = today - timedelta(days=today.weekday() - section.weekday) - timedelta(weeks=weeks_ago)
                if occurrence >= today:
                    continue
                session = AttendanceSession.objects.create(
                    section=section, date=occurrence, opened_by=section.teacher, is_active=False,
                    closed_at=timezone.make_aware(datetime.combine(occurrence, section.end_time)),
                )
                for student in students:
                    if random.random() > 0.14:
                        jitter_lat = settings.CAMPUS_LATITUDE + random.uniform(-0.0004, 0.0004)
                        jitter_lng = settings.CAMPUS_LONGITUDE + random.uniform(-0.0004, 0.0004)
                        distance = haversine_distance_meters(jitter_lat, jitter_lng, settings.CAMPUS_LATITUDE, settings.CAMPUS_LONGITUDE)
                        marked_at = timezone.make_aware(datetime.combine(occurrence, section.start_time) + timedelta(minutes=random.randint(1, 8)))
                        AttendanceRecord.objects.create(
                            session=session, student=student, latitude=jitter_lat, longitude=jitter_lng,
                            distance_meters=distance, device_timestamp=marked_at, marked_at=marked_at,
                        )
                        AttendanceAttempt.objects.create(
                            student=student, session=session, result=AttendanceAttempt.Result.SUCCESS, attempted_at=marked_at,
                            latitude=jitter_lat, longitude=jitter_lng,
                        )
                        present_count += 1
        self.stdout.write(self.style.SUCCESS(f"Created attendance history ({present_count} present records)."))

        # -- Grades ---------------------------------------------------------
        finals_ready = {"CS101", "MATH201"}
        for section_code, section in sections.items():
            for student in students:
                enrollment = Enrollment.objects.get(student=student, section=section)
                Grade.objects.create(
                    enrollment=enrollment,
                    assignment_score=round(random.uniform(72, 97), 1),
                    midterm_score=round(random.uniform(65, 95), 1),
                    final_score=round(random.uniform(65, 96), 1) if section_code in finals_ready else None,
                )

        # -- Achievements -----------------------------------------------------
        potling_profile = students[0].student_profile
        Achievement.objects.create(student=potling_profile, title="Dean's List", icon="🏅",
                                    description="Top 10% of Computer Science, Semester 1", awarded_on=today - timedelta(days=120))
        Achievement.objects.create(student=potling_profile, title="Hackathon Runner-up", icon="🥈",
                                    description="NUM Codefest 2026", awarded_on=today - timedelta(days=60))
        Achievement.objects.create(student=potling_profile, title="Perfect Attendance", icon="🎯",
                                    description="100% attendance in March", awarded_on=today - timedelta(days=30))

        # -- Calendar events --------------------------------------------------
        def make_event(event_type, title, days_from_today, hour, duration_hours, subject_code=None, description=""):
            start = timezone.make_aware(datetime.combine(today + timedelta(days=days_from_today), datetime.min.time()) + timedelta(hours=hour))
            end = start + timedelta(hours=duration_hours)
            return Event.objects.create(
                event_type=event_type, title=title, description=description, start_datetime=start, end_datetime=end,
                subject=subjects[subject_code] if subject_code else None, created_by=admin,
            )

        make_event(Event.EventType.HOLIDAY, "University Rest Day", 9, 0, 24, description="No classes campus-wide.")
        make_event(Event.EventType.UNIVERSITY_EVENT, "NUM Career Fair 2026", 14, 9, 6, description="Meet employers at the Auditorium.")
        make_event(Event.EventType.MIDTERM, "Midterm Exam", 6, 8, 2, "CS102", "Covers chapters 1–5.")
        make_event(Event.EventType.MIDTERM, "Midterm Exam", 7, 10, 2, "MATH201", "Covers sets, logic, and proofs.")
        make_event(Event.EventType.FINAL, "Final Exam", 35, 8, 3, "CS102", "Cumulative, closed book.")
        make_event(Event.EventType.DEADLINE, "Assignment 2 Due", 2, 23, 1, "CS102", "Submit via the course portal.")
        make_event(Event.EventType.DEADLINE, "ER Diagram Project Due", 5, 23, 1, "CS202", "Group submission, 4 members max.")
        make_event(Event.EventType.DEADLINE, "Essay Submission", -2, 23, 1, "ENG101", "Late submissions are not accepted.")

        # Cancel one past occurrence for realism.
        cancelled_date = today - timedelta(days=today.weekday() - sections["CS201"].weekday) - timedelta(weeks=2)
        Event.objects.create(
            event_type=Event.EventType.CLASS_CANCELLED, title="CS201 cancelled", description="Lecturer on leave.",
            start_datetime=timezone.make_aware(datetime.combine(cancelled_date, sections["CS201"].start_time)),
            end_datetime=timezone.make_aware(datetime.combine(cancelled_date, sections["CS201"].end_time)),
            subject=subjects["CS201"], section=sections["CS201"], occurrence_date=cancelled_date, created_by=admin,
        )

        # -- Announcements ------------------------------------------------------
        Announcement.objects.create(
            title="Mid-Semester Break Notice", pinned=True, created_by=admin,
            body="Classes will be suspended university-wide for the mid-semester break. Regular classes resume the following Monday.",
        )
        Announcement.objects.create(
            title="Library Extended Hours During Exam Week", created_by=admin,
            body="The NUM Central Library will stay open until 22:00 during the upcoming exam period.",
        )
        Announcement.objects.create(
            title="NUM Career Fair 2026 — Register Now", created_by=admin,
            body="Over 30 companies will be recruiting at the Auditorium. Register at the Student Services Center.",
        )
        Announcement.objects.create(
            title="Assignment 2 Rubric Updated", created_by=teachers["teacher1"], subject=subjects["CS102"],
            body="The grading rubric for Assignment 2 has been clarified — see the Materials tab.",
        )

        # -- A few notifications for the demo student --------------------------
        Notification.objects.create(user=students[0], notif_type=Notification.NotifType.SCHEDULE_UPDATED,
                                     title="Classroom Changed: Computer Architecture", body="Now in A305")
        Notification.objects.create(user=students[0], notif_type=Notification.NotifType.EXAM_REMINDER,
                                     title="Midterm Exam: Data Structures and Algorithms", body="CS102 — in 6 days")
        Notification.objects.create(user=students[0], notif_type=Notification.NotifType.ANNOUNCEMENT,
                                     title="NUM Career Fair 2026 — Register Now", body="Auditorium · Register at Student Services")

        self.stdout.write(self.style.SUCCESS(
            "\nSeed complete. Log in with student1 / teacher1 / admin1 - password 'num12345' for all."
        ))
