from django.urls import path

from .views import (
    OrderCalendarView,
    OrderCreateView,
    OrderDetailView,
    OrderListView,
    OrderUpdateView,
)

app_name = "orders"

urlpatterns = [
    path("", OrderListView.as_view(), name="order_list"),
    path("calendario/", OrderCalendarView.as_view(), name="calendar"),
    path("nuevo/", OrderCreateView.as_view(), name="order_create"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order_detail"),
    path("<int:pk>/editar/", OrderUpdateView.as_view(), name="order_update"),
]
