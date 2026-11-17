from datetime import timedelta

from django.db.models import F
from django.utils import timezone
from django.views.generic import TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.inventory.models import Ingredient
from apps.orders.models import Order
from apps.production.models import ProductionJob
from apps.quotations.models import Quote
from apps.reports.services import period_result


class DashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()
        if user.has_perm("quotations.view_quote"):
            context["open_quotes"] = Quote.objects.filter(
                status__in=[Quote.Status.DRAFT, Quote.Status.SENT]
            ).count()
        if user.has_perm("orders.view_order"):
            context["week_deliveries"] = Order.objects.filter(
                status__in=[
                    Order.Status.CONFIRMED,
                    Order.Status.IN_PRODUCTION,
                    Order.Status.READY,
                ],
                event_at__date__gte=today,
                event_at__date__lte=today + timedelta(days=6),
            ).count()
        if user.has_perm("production.view_productionjob"):
            context["jobs_today"] = (
                ProductionJob.objects.filter(scheduled_date=today)
                .exclude(order__status=Order.Status.CANCELLED)
                .count()
            )
        if user.has_perm("inventory.view_ingredient"):
            context["low_stock"] = Ingredient.objects.filter(
                reorder_level__gt=0,
                stock_quantity__lte=F("reorder_level"),
            ).count()
        if user.has_perm("inventory.view_expense"):
            context["month_result"] = period_result(today.replace(day=1), today)
        return context
