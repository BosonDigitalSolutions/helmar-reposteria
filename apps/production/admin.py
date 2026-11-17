from django.contrib import admin

from .models import ProductionJob


@admin.register(ProductionJob)
class ProductionJobAdmin(admin.ModelAdmin):
    list_display = ("summary", "order", "scheduled_date", "status")
    list_filter = ("status", "scheduled_date")
