from django.contrib import admin

from .models import Building, Room


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "latitude", "longitude")
    list_filter = ("category",)
    inlines = [RoomInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("code", "building", "capacity")
    list_filter = ("building",)
