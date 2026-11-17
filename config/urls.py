"""Rutas públicas del proyecto."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuenta/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("dashboard/catalogo/", include("apps.catalog.urls")),
    path("dashboard/clientes/", include("apps.crm.urls")),
    path("dashboard/cotizaciones/", include("apps.quotations.urls")),
    path("dashboard/pedidos/", include("apps.orders.urls")),
    path("dashboard/produccion/", include("apps.production.urls")),
    path("dashboard/inventario/", include("apps.inventory.urls")),
    path("dashboard/resultado/", include("apps.reports.urls")),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
