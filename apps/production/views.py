from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.generic import ListView, TemplateView, UpdateView

from apps.accounts.mixins import StaffPermissionMixin
from apps.core.calendar import WEEKDAYS, month_days, month_label, shift_month
from apps.orders.models import Order

from .forms import ProductionJobForm
from .models import ProductionJob
from .services import sync_order_status


class ProductionCalendarView(StaffPermissionMixin, TemplateView):
    permission_required = "production.view_productionjob"
    template_name = "production/calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        try:
            year = int(self.request.GET.get("anio", today.year))
            month = int(self.request.GET.get("mes", today.month))
        except ValueError:
            year, month = today.year, today.month
        if not 1 <= month <= 12:
            year, month = today.year, today.month
        matrix = month_days(year, month)
        grouped = {}
        jobs = (
            ProductionJob.objects.select_related("order__contact")
            .exclude(order__status=Order.Status.CANCELLED)
            .filter(scheduled_date__gte=matrix[0][0], scheduled_date__lte=matrix[-1][-1])
        )
        for job in jobs:
            grouped.setdefault(job.scheduled_date, []).append(job)
        weeks = []
        for week in matrix:
            weeks.append(
                [
                    {
                        "date": day,
                        "in_month": day.month == month,
                        "items": [
                            {
                                "label": f"{job.summary} · {job.order.contact.full_name}",
                                "url": reverse("production:job_detail", args=[job.pk]),
                            }
                            for job in grouped.get(day, [])
                        ],
                    }
                    for day in week
                ]
            )
        context.update(
            {
                "weeks": weeks,
                "weekdays": WEEKDAYS,
                "month_label": month_label(year, month),
                "previous": shift_month(year, month, -1),
                "following": shift_month(year, month, 1),
                "today": today,
                "day_url": reverse("production:day", args=["2000-01-01"]).replace("2000-01-01/", ""),
                "day_tail": "/",
            }
        )
        return context


class ProductionDayView(StaffPermissionMixin, ListView):
    permission_required = "production.view_productionjob"
    template_name = "production/day.html"
    context_object_name = "jobs"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.day = parse_date(kwargs["day"])

    def get_queryset(self):
        return (
            ProductionJob.objects.select_related("order__contact")
            .exclude(order__status=Order.Status.CANCELLED)
            .filter(scheduled_date=self.day)
        )

    def get(self, request, *args, **kwargs):
        if self.day is None:
            messages.error(request, "La fecha no es válida.")
            return redirect("production:calendar")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["day"] = self.day
        return context


class ProductionJobUpdateView(StaffPermissionMixin, UpdateView):
    model = ProductionJob
    form_class = ProductionJobForm
    template_name = "production/job_detail.html"
    context_object_name = "job"

    def get_permission_required(self):
        if self.request.method == "POST":
            return ["production.change_productionjob"]
        return ["production.view_productionjob"]

    def get_queryset(self):
        return ProductionJob.objects.select_related("order__contact", "order_line__product")

    def form_valid(self, form):
        if self.object.order.status == Order.Status.CANCELLED:
            messages.error(self.request, "El pedido está cancelado. La ficha ya no se mueve.")
            return redirect("production:job_detail", pk=self.object.pk)
        self.object = form.save()
        sync_order_status(self.object.order)
        messages.success(self.request, "La ficha de cocina se actualizó.")
        return redirect("production:job_detail", pk=self.object.pk)
