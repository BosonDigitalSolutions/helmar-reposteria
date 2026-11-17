from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from apps.accounts.mixins import StaffPermissionMixin
from apps.core.folios import next_folio
from apps.core.lines import active_lines, subtotal_from_lines

from .forms import QuoteForm, QuoteLineFormSet
from .models import Quote
from .services import (
    accept_quote,
    expire_quote,
    mark_quote_pending,
    refresh_totals,
    reject_quote,
    rush_warning,
    send_quote,
    whatsapp_message,
)


class QuoteListView(StaffPermissionMixin, ListView):
    permission_required = "quotations.view_quote"
    template_name = "quotations/quote_list.html"
    context_object_name = "quotes"
    paginate_by = 12

    def get_queryset(self):
        quotes = Quote.objects.select_related("contact")
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("estado", "").strip()
        if query:
            quotes = quotes.filter(
                Q(folio__icontains=query)
                | Q(contact__first_name__icontains=query)
                | Q(contact__last_name__icontains=query)
            )
        if status in Quote.Status.values:
            quotes = quotes.filter(status=status)
        return quotes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["filters"] = params.urlencode()
        context["statuses"] = Quote.Status.choices
        return context


class QuoteFormMixin(StaffPermissionMixin):
    model = Quote
    form_class = QuoteForm
    template_name = "quotations/quote_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, "line_formset"):
            context["lines"] = self.line_formset
        else:
            context["lines"] = QuoteLineFormSet(
                self.request.POST or None,
                instance=self.object or Quote(),
                prefix="lines",
            )
        return context

    def form_valid(self, form):
        self.line_formset = QuoteLineFormSet(
            self.request.POST,
            instance=self.object or Quote(),
            prefix="lines",
        )
        if not self.line_formset.is_valid():
            return self.form_invalid(form)
        subtotal = subtotal_from_lines(active_lines(self.line_formset))
        if form.cleaned_data["discount"] > subtotal:
            form.add_error("discount", "El descuento no puede superar el subtotal.")
            return self.form_invalid(form)
        previous = self.object.status if self.object and self.object.pk else None
        with transaction.atomic():
            self.object = form.save(commit=False)
            if not self.object.folio:
                self.object.folio = next_folio("COT")
            if previous == Quote.Status.SENT:
                self.object.status = Quote.Status.DRAFT
            if not self.object.created_by_id:
                self.object.created_by = self.request.user
            self.object.save()
            self.line_formset.instance = self.object
            self.line_formset.save()
            refresh_totals(self.object)
            mark_quote_pending(self.object, self.request.user)
        messages.success(self.request, "La cotización se guardó.")
        if previous == Quote.Status.SENT:
            messages.info(self.request, "Volvió a borrador. Envíala de nuevo para congelar la versión.")
        return redirect("quotations:quote_detail", pk=self.object.pk)


class QuoteCreateView(QuoteFormMixin, CreateView):
    permission_required = "quotations.add_quote"


class QuoteUpdateView(QuoteFormMixin, UpdateView):
    permission_required = "quotations.change_quote"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_editable:
            messages.error(request, "Esta cotización ya no se puede editar.")
            return redirect("quotations:quote_detail", pk=self.object.pk)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_editable:
            messages.error(request, "Esta cotización ya no se puede editar.")
            return redirect("quotations:quote_detail", pk=self.object.pk)
        return super().post(request, *args, **kwargs)


class QuoteDetailView(StaffPermissionMixin, DetailView):
    permission_required = "quotations.view_quote"
    model = Quote
    template_name = "quotations/quote_detail.html"
    context_object_name = "quote"

    def get_queryset(self):
        return Quote.objects.select_related("contact", "opportunity").prefetch_related(
            "lines__product",
            "revisions",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["warning"] = rush_warning(self.object)
        context["whatsapp_text"] = whatsapp_message(self.object)
        context["past_validity"] = bool(
            self.object.valid_until and self.object.valid_until < timezone.localdate()
        )
        return context


class QuoteActionView(StaffPermissionMixin, View):
    permission_required = "quotations.change_quote"
    action = None

    def post(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk)
        try:
            result = self.action(quote, request.user)
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
            return redirect("quotations:quote_detail", pk=quote.pk)
        if self.action is accept_quote:
            messages.success(request, "La cotización se aceptó y el pedido quedó confirmado.")
            return redirect("orders:order_detail", pk=result.pk)
        messages.success(request, "La cotización se actualizó.")
        return redirect("quotations:quote_detail", pk=quote.pk)


class QuoteSendView(QuoteActionView):
    action = staticmethod(send_quote)


class QuoteAcceptView(QuoteActionView):
    action = staticmethod(accept_quote)


class QuoteRejectView(QuoteActionView):
    action = staticmethod(reject_quote)


class QuoteExpireView(QuoteActionView):
    action = staticmethod(expire_quote)
