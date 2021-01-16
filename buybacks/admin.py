from django.contrib import admin


from .models import Corporation, Location, Office

# Register your models here.


@admin.register(Corporation)
class CorporationAdmin(admin.ModelAdmin):
    list_display = ("character", "corporation")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "eve_solar_system")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ("id", "corporation", "location")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
