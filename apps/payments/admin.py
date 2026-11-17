from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "kind", "method", "amount", "paid_on")
    list_filter = ("kind", "method")
