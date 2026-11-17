from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Cuentas"

    def ready(self):
        post_migrate.connect(sync_role_groups, dispatch_uid="accounts.sync_role_groups")


def sync_role_groups(sender, **kwargs):
    from django.contrib.auth.models import Group, Permission
    from django.db import connection

    tables = set(connection.introspection.table_names())
    if "auth_group" not in tables or "auth_permission" not in tables:
        return

    from apps.accounts.roles import ROLE_GROUP_NAMES

    for name in ROLE_GROUP_NAMES.values():
        Group.objects.get_or_create(name=name)
    admin_group = Group.objects.get(name=ROLE_GROUP_NAMES["administrador"])
    sales_group = Group.objects.get(name=ROLE_GROUP_NAMES["ventas"])
    production_group = Group.objects.get(name=ROLE_GROUP_NAMES["produccion"])
    admin_group.permissions.set(Permission.objects.all())
    sales_group.permissions.set(
        Permission.objects.filter(content_type__app_label="crm").exclude(
            content_type__model="crmsettings"
        )
        | Permission.objects.filter(
            content_type__app_label="catalog",
            codename__startswith="view_",
        )
        | Permission.objects.filter(
            content_type__app_label__in=["quotations", "orders", "payments"]
        )
        | Permission.objects.filter(
            content_type__app_label="production",
            codename__startswith="view_",
        )
    )
    production_group.permissions.set(
        Permission.objects.filter(
            content_type__app_label="catalog",
            codename__startswith="view_",
        )
        | Permission.objects.filter(
            content_type__app_label="production",
            codename__in=["view_productionjob", "change_productionjob"],
        )
        | Permission.objects.filter(
            content_type__app_label="inventory",
            codename="view_ingredient",
        )
    )
