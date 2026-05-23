from django.contrib import admin

from apps.orders.models import Order, OrderItem, Rating


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["service_name_en", "service_name_ar", "unit_price", "total_price"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "nurse", "status", "final_price", "created_at"]
    list_filter = ["status", "area", "created_at", "completed_at"]
    search_fields = ["id", "patient__email", "nurse__email", "address"]
    readonly_fields = ["services_subtotal", "final_price", "created_at", "updated_at"]
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "service_name_en", "quantity", "unit_price", "total_price"]
    search_fields = ["order__id", "service_name_en", "service_name_ar"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["order", "patient", "nurse", "score", "created_at"]
    list_filter = ["score", "created_at"]
    search_fields = ["order__id", "patient__email", "nurse__email", "comment"]
    readonly_fields = ["created_at", "updated_at"]
