"""
Django settings for the NUM Student Portal.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-^komymcosnbk5!0yy8fnknpb_wmt_=nq^3b^+)mil3gfl(5w$8",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = ["*"] if DEBUG else os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

# Render sets this to the service's onrender.com hostname automatically.
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Railway sets this to the service's up.railway.app hostname automatically once a
# public domain has been generated for it.
RAILWAY_PUBLIC_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)

CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin
]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")
if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_PUBLIC_DOMAIN}")

if DEBUG:
    # Allow the Cloudflare quick-tunnel (or any similar HTTPS dev tunnel) to submit
    # forms without CSRF "Origin checking failed" errors, since cloudflared terminates
    # TLS and forwards plain HTTP to this dev server.
    CSRF_TRUSTED_ORIGINS.append("https://*.trycloudflare.com")

# Render (like the Cloudflare tunnel above) terminates TLS at the proxy and forwards
# plain HTTP internally, so Django needs this header to know the original request was HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    "accounts",
    "academics",
    "calendar_app",
    "attendance",
    "grades",
    "notifications",
    "campus",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "numportal.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "notifications.context_processors.notifications_context",
            ],
        },
    },
]

WSGI_APPLICATION = "numportal.wsgi.application"


DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Phnom_Penh"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard_redirect"
LOGOUT_REDIRECT_URL = "accounts:login"

# ---------------------------------------------------------------------------
# NUM Student Portal specific settings
# ---------------------------------------------------------------------------

# Google Maps JavaScript API key for the Campus Map page.
# Get one at https://console.cloud.google.com/google/maps-apis and set it as
# an environment variable before deploying. The Campus Map page degrades to a
# building list view automatically when this is empty.
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

# National University of Management - Veal Sbov Campus, Phnom Penh, Cambodia.
CAMPUS_NAME = "National University of Management — Veal Sbov Campus"
CAMPUS_LATITUDE = float(os.environ.get("CAMPUS_LATITUDE", "11.522554"))
CAMPUS_LONGITUDE = float(os.environ.get("CAMPUS_LONGITUDE", "104.965866"))
# Attendance is only accepted inside this radius of the campus center (meters).
CAMPUS_ATTENDANCE_RADIUS_METERS = 150

# QR attendance token lifetime, in seconds. Regenerated automatically on the
# teacher's screen just before expiry so a screenshotted code goes stale fast.
ATTENDANCE_QR_TTL_SECONDS = 45

# Minutes of grace before/after a class's scheduled time window during which
# attendance scans are still accepted.
ATTENDANCE_GRACE_MINUTES_BEFORE = 15
ATTENDANCE_GRACE_MINUTES_AFTER = 20
