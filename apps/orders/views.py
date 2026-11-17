from django.contrib import messages
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from apps.accounts.mixins import StaffPermissionMixin
from apps.core.calendar import WEEKDAYS, month_days, month_label, shift_month
from apps.core.folios import next_folio
from apps.core.lines import active_lines, subtotal_from_lines
from apps.payments.forms import PaymentForm
from apps.payments.services import register_payment
from apps.production.services import create_jobs, refresh_open_prep_dates

from .forms import OrderForm, OrderHeaderForm, OrderLineFormSet
from .models import Order
from .services import refresh_totals


class OrderQueryMixin:
    def filtered_orders(self):
        orders = Order.objects.select_related("contact")
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("estado", "").strip()
        day = parse_date(self.request.GET.get("fecha", "").strip())
        if query:
            orders = orders.filter(
                Q(folio__icontains=query)
                | Q(contact__first_name__icontains=query)
                | Q(contact__last_name__icontains=query)
            )
        if status in Order.Status.values:
            orders = orders.filter(status=status)
        if day:
            orders = orders.filter(event_at__date=day)
        return orders, day


class OrderListView(StaffPermissionMixin, OrderQueryMixin, ListView):
    permission_required = "orders.view_order"
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 12

    def get_queryset(self):
        orders, self.selected_day = self.filtered_orders()
        return orders

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["filters"] = params.urlencode()
        context["statuses"] = Order.Status.choices
        context["selected_day"] = self.selected_day
        return context


class OrderCalendarView(StaffPermissionMixin, TemplateView):
    permission_required = "orders.view_order"
    template_name = "orders/calendar.html"

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
        orders = Order.objects.select_related("contact").filter(
            event_at__date__gte=matrix[0][0],
            event_at__date__lte=matrix[-1][-1],
        )
        for order in orders:
            grouped.setdefault(timezone.localtime(order.event_at).date(), []).append(order)
        weeks = []
        for week in matrix:
            weeks.append(
                [
                    {
                        "date": day,
                        "in_month": day.month == month,
                        "items": [
                            {
                                "label": f"{order.folio} · {order.contact.full_name}",
                                "url": reverse("orders:order_detail", args=[order.pk]),
                            }
                            for order in grouped.get(day, [])
                        ],
                    }
                    for day in week
                ]
            )
        previous = shift_month(year, month, -1)
        following = shift_month(year, month, 1)
        context.update(
            {
                "weeks": weeks,
                "weekdays": WEEKDAYS,
                "month_label": month_label(year, month),
                "previous": previous,
                "following": following,
                "today": today,
                "day_url": reverse("orders:order_list") + "?fecha=",
                "day_tail": "",
            }
        )
        return context


class OrderCreateView(StaffPermissionMixin, CreateView):
    permission_required = "orders.add_order"
    model = Order
    form_class = OrderForm
    template_name = "orders/order_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, "line_formset"):
            context["lines"] = self.line_formset
        else:
            context["lines"] = OrderLineFormSet(
                self.request.POST or None,
                instance=self.object or Order(),
                prefix="lines",
            )
        return context

    def form_valid(self, form):
        self.line_formset = OrderLineFormSet(
            self.request.POST,
            instance=self.object or Order(),
            prefix="lines",
        )
        if not self.line_formset.is_valid():
            return self.form_invalid(form)
        subtotal = subtotal_from_lines(active_lines(self.line_formset))
        if form.cleaned_data["discount"] > subtotal:
            form.add_error("discount", "El descuento no puede superar el subtotal.")
            return self.form_invalid(form)
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.folio = next_folio("PED")
            self.object.status = Order.Status.CONFIRMED
            self.object.created_by = self.request.user
            self.object.save()
            self.line_formset.instance = self.object
            self.line_formset.save()
            refresh_totals(self.object)
            create_jobs(self.object)
        messages.success(self.request, "El pedido quedó confirmado y la cocina ya tiene sus fichas.")
        return redirect("orders:order_detail", pk=self.object.pk)


class OrderUpdateView(StaffPermissionMixin, UpdateView):
    permission_required = "orders.change_order"
    model = Order
    form_class = OrderHeaderForm
    template_name = "orders/order_form.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_open:
            messages.error(request, "Este pedido ya no se puede modificar.")
            return redirect("orders:order_detail", pk=self.object.pk)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_open:
            messages.error(request, "Este pedido ya no se puede modificar.")
            return redirect("orders:order_detail", pk=self.object.pk)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            refresh_open_prep_dates(self.object)
        messages.success(self.request, "La entrega se actualizó.")
        return redirect("orders:order_detail", pk=self.object.pk)


class OrderDetailView(StaffPermissionMixin, DetailView):
    permission_required = "orders.view_order"
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.select_related("contact", "quote").prefetch_related(
            "lines__product",
            "payments",
            "jobs",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payment_form"] = kwargs.get("payment_form") or PaymentForm(
            initial={"paid_on": timezone.localdate()}
        )
        context["warning"] = self._warning()
        return context

    def _warning(self) -> str:
        event_date = timezone.localtime(self.object.event_at).date()
        needed = [
            line.product.lead_time_days
            for line in self.object.lines.select_related("product")
            if line.product_id
        ]
        if not needed:
            return ""
        minimum = max(needed)
        days_until = (event_date - timezone.localdate()).days
        if days_until < minimum:
            return (
                f"La entrega está a {days_until} días y hay una pieza que pide "
                f"{minimum} de anticipación."
            )
        return ""

    def post(self, request, pk):
        self.object = self.get_object()
        action = request.POST.get("accion")
        if action == "cobro":
            return self._collect(request)
        if action == "entregar":
            return self._deliver(request)
        if action == "cancelar":
            return self._cancel(request)
        messages.error(request, "La acción no es válida.")
        return redirect("orders:order_detail", pk=self.object.pk)

    def _collect(self, request):
        if not request.user.has_perm("payments.add_payment"):
            return HttpResponseForbidden()
        form = PaymentForm(request.POST)
        if not form.is_valid():
            context = self.get_context_data(payment_form=form)
            return self.render_to_response(context)
        try:
            register_payment(
                self.object,
                amount=form.cleaned_data["amount"],
                kind=form.cleaned_data["kind"],
                method=form.cleaned_data["method"],
                paid_on=form.cleaned_data["paid_on"],
                note=form.cleaned_data["note"],
                user=request.user,
            )
        except ValidationError as exc:
            if hasattr(exc, "error_dict"):
                for field, errors in exc.error_dict.items():
                    for error in errors:
                        form.add_error(field if field in form.fields else None, error)
            else:
                form.add_error(None, " ".join(exc.messages))
            return self.render_to_response(self.get_context_data(payment_form=form))
        messages.success(request, "El cobro quedó registrado.")
        return redirect("orders:order_detail", pk=self.object.pk)

    def _deliver(self, request):
        if not request.user.has_perm("orders.change_order"):
            return HttpResponseForbidden()
        if self.object.status != Order.Status.READY:
            messages.error(request, "La cocina todavía no marca el pedido como listo.")
            return redirect("orders:order_detail", pk=self.object.pk)
        self.object.status = Order.Status.DELIVERED
        self.object.save(update_fields=["status", "updated_at"])
        messages.success(request, "El pedido se marcó como entregado.")
        return redirect("orders:order_detail", pk=self.object.pk)

    def _cancel(self, request):
        if not request.user.has_perm("orders.change_order"):
            return HttpResponseForbidden()
        if self.object.status in {Order.Status.DELIVERED, Order.Status.CANCELLED}:
            messages.error(request, "Este pedido ya no se puede cancelar.")
            return redirect("orders:order_detail", pk=self.object.pk)
        self.object.status = Order.Status.CANCELLED
        self.object.save(update_fields=["status", "updated_at"])
        messages.success(request, "El pedido se canceló.")
        return redirect("orders:order_detail", pk=self.object.pk)
