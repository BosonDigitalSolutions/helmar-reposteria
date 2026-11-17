from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User

admin.site.site_header = "HelyMar Repostería"
admin.site.site_title = "HelyMar"
admin.site.index_title = "Administración"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Rol en HelyMar", {"fields": ("role",)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Rol en HelyMar", {"fields": ("role", "email")}),
    )
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)
