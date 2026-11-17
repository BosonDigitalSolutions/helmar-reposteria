from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.generic import TemplateView

from apps.accounts.mixins import StaffPermissionMixin

from .services import period_result


class ResultView(StaffPermissionMixin, TemplateView):
    permission_required = "inventory.view_expense"
    template_name = "reports/result.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        start = parse_date(self.request.GET.get("desde", "")) or today.replace(day=1)
        end = parse_date(self.request.GET.get("hasta", "")) or today
        if start > end:
            messages.error(self.request, "La fecha inicial no puede ser posterior a la final.")
            start, end = end, start
        context["start"] = start
        context["end"] = end
        context["result"] = period_result(start, end)
        return context
