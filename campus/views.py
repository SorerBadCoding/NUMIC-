from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Building


@login_required
def campus_map(request):
    buildings = list(Building.objects.prefetch_related("rooms"))
    buildings_data = [
        {
            "id": b.id,
            "code": b.code,
            "name": b.name,
            "category": b.get_category_display(),
            "icon": b.icon,
            "lat": b.latitude,
            "lng": b.longitude,
            "departments": b.department_list,
            "hours": b.opening_hours,
            "description": b.description,
        }
        for b in buildings
    ]

    context = {
        "active_nav": "campus_map",
        "buildings": buildings,
        "buildings_data": buildings_data,
        "google_maps_key": settings.GOOGLE_MAPS_API_KEY,
        "campus_lat": settings.CAMPUS_LATITUDE,
        "campus_lng": settings.CAMPUS_LONGITUDE,
        "campus_name": settings.CAMPUS_NAME,
    }
    return render(request, "campus/map.html", context)
