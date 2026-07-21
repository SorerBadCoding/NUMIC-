# NUM Student Portal

A redesigned Student Management Portal for the **National University of Management** —
Veal Sbov Campus. Django + Bootstrap 5 backend/frontend, QR + GPS attendance,
Google Maps campus navigation, and a role-based calendar (Student / Teacher / Admin).

## Setup

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py seed_data     # demo data (skips if already seeded)
.venv\Scripts\python manage.py runserver
```

Open http://127.0.0.1:8000/ and sign in with any of the demo accounts
(password `num12345` for all):

| Role    | Username     |
|---------|--------------|
| Student | `student1` … `student14` |
| Teacher | `teacher1` … `teacher4`  |
| Admin   | `admin1` (also a Django superuser — `/admin/`) |

`student1` is the primary demo account ("Potling"), enrolled in all 9 seeded subjects
with grades, attendance history, achievements, and notifications populated.

To start over with a clean database, delete `db.sqlite3` and re-run `migrate` + `seed_data`.

## Enabling the live Campus Map

The Campus Map page works out of the box as a building directory. To enable the
interactive Google Map with walking directions and ETA, set an API key with the
Maps JavaScript API + Directions API enabled:

```bash
set GOOGLE_MAPS_API_KEY=your-key-here      # Windows cmd
$env:GOOGLE_MAPS_API_KEY="your-key-here"   # PowerShell
```

Without a key, the page degrades gracefully to a building list.

## Deploying to Render

This repo includes a `render.yaml` Blueprint that provisions a web service + a
Postgres database together.

1. Push this repo to GitHub (it isn't a git repo yet — see below).
2. In the [Render dashboard](https://dashboard.render.com), click **New > Blueprint**
   and point it at the repo. Render reads `render.yaml` and creates:
   - a **free Postgres** database (`numportal-db`)
   - a **free web service** (`numportal`) that runs `build.sh` (install deps,
     collect static files, migrate, seed demo data) then starts with `gunicorn`.
3. `DJANGO_SECRET_KEY` and `DATABASE_URL` are wired up automatically. Set
   `GOOGLE_MAPS_API_KEY` yourself in the service's **Environment** tab (it's marked
   `sync: false` so it isn't stored in the repo) — use the same key from your local `.env`.
4. Once deployed, your site is live at `https://numportal-<random>.onrender.com`.
   `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` pick this up automatically via Render's
   `RENDER_EXTERNAL_HOSTNAME` env var — no config needed. If you attach a custom
   domain later, add it to a `DJANGO_ALLOWED_HOSTS` env var (comma-separated) and to
   `DJANGO_CSRF_TRUSTED_ORIGINS` (as a full `https://...` origin).

Notes:
- Render's **free** Postgres instances are deleted after 30 days — fine for a demo,
  but upgrade to a paid plan (or re-provision) before that if you need it to persist.
- Free web services spin down after inactivity, so the first request after a while
  will be slow (~30-60s cold start).
- QR/camera-based attendance requires HTTPS, which Render provides automatically.

## Architecture

Seven Django apps, one per feature area:

- **accounts** — custom `User` model with `role` (student/teacher/admin), `StudentProfile`,
  `TeacherProfile`, `Achievement`, role-based dashboards and auth.
- **academics** — `Subject`, `ClassSection` (recurring weekly schedule), `Enrollment`, `Material`.
- **campus** — `Building` / `Room` used by both scheduling and the Campus Map.
- **calendar_app** — `Event` model for exams/deadlines/holidays/university events/cancellations.
  Regular weekly classes are generated on the fly from `ClassSection` and merged with `Event`
  overrides (cancel / "No Class Today") — see `calendar_app/services.py`.
- **attendance** — QR + GPS check-in. See "Attendance security" below.
- **grades** — per-subject `Grade` (assignments/midterm/final) and credit-weighted GPA.
- **notifications** — `Announcement` (admin/teacher broadcasts) and per-user `Notification`.

Templates live in `templates/`, one folder per app, extending `templates/base.html`. All
styling is a single hand-written design system at `static/css/theme.css` (no CSS framework
beyond Bootstrap 5 for grid/modals/forms) — rounded cards, soft shadows, blue gradient accents.

## Attendance security model

QR codes are generated server-side (`attendance/qr.py`, using the `qrcode` package) and
signed with `django.core.signing.TimestampSigner` (`attendance/views.py`). A scan is only
accepted if **all** of the following hold:

1. Signature is valid and not expired (`ATTENDANCE_QR_TTL_SECONDS`, default 45s).
2. The underlying `QRToken` hasn't already been consumed (single-use — defeats screenshot reuse).
3. The attendance session is still open (teacher hasn't closed it).
4. The scanning student is enrolled in that class's subject.
5. The current time falls within the class's scheduled window (± grace minutes).
6. The student hasn't already been marked present for that session.
7. The student's browser-reported GPS coordinates are within `CAMPUS_ATTENDANCE_RADIUS_METERS`
   (default 150m) of the campus center, via the haversine formula (`attendance/utils.py`).
8. The device's reported timestamp roughly matches server time (clock-tamper check).

Every attempt — success or failure, with a specific reason — is logged to `AttendanceAttempt`
for audit purposes. All of this is configurable in `numportal/settings.py` under
"NUM Student Portal specific settings".

## Known scope notes

- The Campus Map's "My Location → walking route" needs a real Google Maps API key to render;
  the building directory works without one.
- QR scanning (`attendance/scan/`) requires camera access and HTTPS (or `localhost`) in real
  browsers — Chrome blocks camera on plain HTTP for non-localhost hosts.
- This build keeps a single SQLite database for simplicity; swap `DATABASES` in
  `numportal/settings.py` for PostgreSQL in production (the model layer is unchanged).
