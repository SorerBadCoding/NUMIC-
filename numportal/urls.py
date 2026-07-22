from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("manifest.webmanifest", views.manifest_view, name="manifest"),
    path("sw.js", views.service_worker_view, name="service_worker"),
    path("offline/", views.offline_view, name="offline"),
    path("", include("accounts.urls")),
    path("calendar/", include("calendar_app.urls")),
    path("attendance/", include("attendance.urls")),
    path("subjects/", include("academics.urls")),
    path("campus-map/", include("campus.urls")),
    path("grades/", include("grades.urls")),
    path("notifications/", include("notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
