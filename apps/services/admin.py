from django.contrib import admin

from apps.services.models import Area, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name_en", "name_ar", "price", "is_active", "is_deleted", "created_at"]
    list_filter = ["is_active", "is_deleted", "created_at"]
    search_fields = ["name_en", "name_ar", "description_en", "description_ar"]
    readonly_fields = ["created_at", "updated_at", "deleted_at"]


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ["name_en", "name_ar", "transportation_fee", "is_active", "is_deleted", "created_at"]
    list_filter = ["is_active", "is_deleted", "created_at"]
    search_fields = ["name_en", "name_ar"]
    readonly_fields = ["created_at", "updated_at", "deleted_at"]
