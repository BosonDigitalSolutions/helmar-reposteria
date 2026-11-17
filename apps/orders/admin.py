from django.contrib import admin

from .models import Order, OrderLine


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("folio", "contact", "status", "event_at", "total")
    list_filter = ("status", "delivery_type")
    search_fields = ("folio", "contact__first_name", "contact__last_name")
    inlines = [OrderLineInline]
