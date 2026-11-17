from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView, View

from apps.accounts.mixins import StaffPermissionMixin

from .forms import (
    ActivityForm,
    ContactForm,
    CrmSettingsForm,
    ImportUploadForm,
    NoteForm,
    OpportunityForm,
)
from .models import (
    Activity,
    Contact,
    ContactStatusLog,
    CrmSettings,
    ImportBatch,
    ImportRow,
    Note,
    Opportunity,
    OpportunityStageLog,
    Tag,
)
from .services import find_matches, parse_contact_csv, validate_payload


def record_contact_status(contact, previous, user):
    if previous == contact.status:
        return
    ContactStatusLog.objects.create(
        contact=contact,
        from_status=previous or "",
        to_status=contact.status,
        changed_by=user,
    )


class ContactListView(StaffPermissionMixin, ListView):
    permission_required = "crm.view_contact"
    template_name = "crm/contact_list.html"
    context_object_name = "contacts"
    paginate_by = 12

    def get_queryset(self):
        contacts = Contact.objects.select_related("owner")
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("estado", "").strip()
        if query:
            contacts = contacts.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(phone__icontains=query)
                | Q(company__icontains=query)
            )
        if status in Contact.Status.values:
            contacts = contacts.filter(status=status)
        if self.request.GET.get("seguimiento") == "pendiente":
            contacts = contacts.filter(
                next_follow_up__isnull=False,
                next_follow_up__lte=timezone.localdate(),
            )
        return contacts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["filters"] = params.urlencode()
        context["statuses"] = Contact.Status.choices
        return context


class ContactCreateView(StaffPermissionMixin, CreateView):
    permission_required = "crm.add_contact"
    model = Contact
    form_class = ContactForm
    template_name = "crm/contact_form.html"

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            record_contact_status(self.object, "", self.request.user)
        messages.success(self.request, "El contacto se registró.")
        return redirect("crm:contact_detail", pk=self.object.pk)


class ContactUpdateView(StaffPermissionMixin, UpdateView):
    permission_required = "crm.change_contact"
    model = Contact
    form_class = ContactForm
    template_name = "crm/contact_form.html"

    def form_valid(self, form):
        previous = Contact.objects.get(pk=self.object.pk).status
        with transaction.atomic():
            self.object = form.save()
            record_contact_status(self.object, previous, self.request.user)
        messages.success(self.request, "El contacto se actualizó.")
        return redirect("crm:contact_detail", pk=self.object.pk)


class ContactDetailView(StaffPermissionMixin, DetailView):
    permission_required = "crm.view_contact"
    model = Contact
    template_name = "crm/contact_detail.html"
    context_object_name = "contact"

    def get_queryset(self):
        return Contact.objects.select_related("owner").prefetch_related(
            "tags",
            "notes",
            "activities",
            "opportunities",
            "status_logs",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["note_form"] = NoteForm()
        context["activity_form"] = ActivityForm()
        context["today"] = timezone.localdate()
        return context


class ContactDeleteView(StaffPermissionMixin, DeleteView):
    permission_required = "crm.delete_contact"
    model = Contact
    template_name = "components/confirm_delete.html"
    success_url = reverse_lazy("crm:contact_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse("crm:contact_detail", args=[self.object.pk])
        context["object_label"] = self.object.full_name
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "No se puede eliminar el contacto porque tiene oportunidades.",
            )
            return redirect("crm:contact_detail", pk=self.object.pk)
        messages.success(self.request, "El contacto se eliminó.")
        return response


class NoteCreateView(StaffPermissionMixin, View):
    permission_required = "crm.add_note"

    def post(self, request, pk):
        contact = get_object_or_404(Contact, pk=pk)
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.contact = contact
            note.author = request.user
            note.save()
            messages.success(request, "La nota se guardó.")
        else:
            messages.error(request, "No se pudo guardar la nota.")
        return redirect("crm:contact_detail", pk=contact.pk)


class ActivityCreateView(StaffPermissionMixin, View):
    permission_required = "crm.add_activity"

    def post(self, request, pk):
        contact = get_object_or_404(Contact, pk=pk)
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.contact = contact
            activity.author = request.user
            activity.save()
            messages.success(request, "La actividad se registró.")
        else:
            messages.error(request, "No se pudo registrar la actividad.")
        return redirect("crm:contact_detail", pk=contact.pk)


def pipeline_context():
    opportunities = Opportunity.objects.select_related("contact", "owner")
    columns = []
    for value, label in Opportunity.Stage.choices:
        columns.append(
            {
                "value": value,
                "label": label,
                "cards": [item for item in opportunities if item.stage == value],
            }
        )
    return {"columns": columns, "stages": Opportunity.Stage.choices}


class OpportunityBoardView(StaffPermissionMixin, View):
    permission_required = "crm.view_opportunity"
    template_name = "crm/opportunity_board.html"

    def get(self, request):
        return render(request, self.template_name, pipeline_context())


class OpportunityCreateView(StaffPermissionMixin, CreateView):
    permission_required = "crm.add_opportunity"
    model = Opportunity
    form_class = OpportunityForm
    template_name = "crm/opportunity_form.html"

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            OpportunityStageLog.objects.create(
                opportunity=self.object,
                from_stage="",
                to_stage=self.object.stage,
                changed_by=self.request.user,
            )
        messages.success(self.request, "La oportunidad se creó.")
        return redirect("crm:opportunity_board")


class OpportunityMoveView(StaffPermissionMixin, View):
    permission_required = "crm.change_opportunity"

    def post(self, request, pk):
        opportunity = get_object_or_404(Opportunity, pk=pk)
        stage = request.POST.get("stage", "")
        if stage not in Opportunity.Stage.values:
            messages.error(request, "La etapa no es válida.")
        elif stage != opportunity.stage:
            previous = opportunity.stage
            with transaction.atomic():
                opportunity.stage = stage
                opportunity.save(update_fields=["stage", "updated_at"])
                OpportunityStageLog.objects.create(
                    opportunity=opportunity,
                    from_stage=previous,
                    to_stage=stage,
                    changed_by=request.user,
                )
            messages.success(request, "La etapa se actualizó.")
        if request.headers.get("HX-Request"):
            return render(request, "crm/pipeline_board.html", pipeline_context())
        return redirect("crm:opportunity_board")


class CrmSettingsUpdateView(StaffPermissionMixin, UpdateView):
    permission_required = "crm.change_crmsettings"
    form_class = CrmSettingsForm
    template_name = "crm/settings_form.html"
    success_url = reverse_lazy("crm:settings")

    def get_object(self, queryset=None):
        return CrmSettings.load()

    def form_valid(self, form):
        messages.success(self.request, "Las reglas de duplicados se guardaron.")
        return super().form_valid(form)


class ImportUploadView(StaffPermissionMixin, FormView):
    permission_required = "crm.add_contact"
    form_class = ImportUploadForm
    template_name = "crm/import_upload.html"

    def form_valid(self, form):
        uploaded = form.cleaned_data["archivo"]
        try:
            parsed = parse_contact_csv(uploaded)
        except ValueError as exc:
            form.add_error("archivo", str(exc))
            return self.form_invalid(form)
        rules = CrmSettings.load()
        with transaction.atomic():
            batch = ImportBatch.objects.create(
                created_by=self.request.user,
                original_name=uploaded.name,
            )
            for line_number, payload in parsed:
                errors = validate_payload(payload)
                matches = []
                if not errors:
                    matches = find_matches(
                        email=payload.get("email", ""),
                        phone=payload.get("phone", ""),
                        whatsapp=payload.get("whatsapp", ""),
                        settings=rules,
                    )
                action = ImportRow.Action.CREATE
                if errors or matches:
                    action = ImportRow.Action.SKIP
                ImportRow.objects.create(
                    batch=batch,
                    line_number=line_number,
                    payload=payload,
                    errors=errors,
                    match_ids=[match.pk for match in matches],
                    action=action,
                )
        return redirect("crm:import_preview", pk=batch.pk)


class ImportPreviewView(StaffPermissionMixin, View):
    permission_required = "crm.add_contact"
    template_name = "crm/import_preview.html"

    def get_batch(self, pk):
        return get_object_or_404(
            ImportBatch.objects.prefetch_related("rows"),
            pk=pk,
            confirmed_at__isnull=True,
        )

    def get(self, request, pk):
        batch = self.get_batch(pk)
        return render(
            request,
            self.template_name,
            {"batch": batch},
        )


class ImportConfirmView(StaffPermissionMixin, View):
    permission_required = "crm.add_contact"

    def post(self, request, pk):
        batch = get_object_or_404(ImportBatch, pk=pk, confirmed_at__isnull=True)
        created = 0
        skipped = 0
        with transaction.atomic():
            for row in batch.rows.select_for_update().order_by("line_number"):
                if row.errors:
                    row.action = ImportRow.Action.SKIP
                else:
                    chosen = request.POST.get(f"action-{row.pk}", row.action)
                    if chosen not in ImportRow.Action.values:
                        chosen = ImportRow.Action.SKIP
                    row.action = chosen
                row.save(update_fields=["action"])
                if row.errors or row.action != ImportRow.Action.CREATE:
                    skipped += 1
                    continue
                payload = row.payload
                matches = find_matches(
                    email=payload.get("email", ""),
                    phone=payload.get("phone", ""),
                    whatsapp=payload.get("whatsapp", ""),
                )
                known_ids = set(row.match_ids)
                if any(match.pk not in known_ids for match in matches):
                    skipped += 1
                    continue
                try:
                    contact = Contact.objects.create(
                        first_name=payload["first_name"],
                        last_name=payload.get("last_name", ""),
                        email=payload.get("email", ""),
                        phone=payload.get("phone", ""),
                        whatsapp=payload.get("whatsapp", ""),
                        company=payload.get("company", ""),
                        origin=payload["origin"],
                        status=payload.get("status") or Contact.Status.LEAD,
                        observations=payload.get("notes", ""),
                        owner=request.user,
                    )
                except IntegrityError:
                    skipped += 1
                    continue
                tag_names = [
                    name.strip()
                    for name in payload.get("tags", "").split(",")
                    if name.strip()
                ]
                if tag_names:
                    contact.tags.set([Tag.objects.get_or_create(name=name)[0] for name in tag_names])
                record_contact_status(contact, "", request.user)
                created += 1
            batch.confirmed_at = timezone.now()
            batch.save(update_fields=["confirmed_at"])
        messages.success(
            request,
            f"Se importaron {created} contactos. Se omitieron {skipped}. No se fusionó ningún registro.",
        )
        return redirect("crm:contact_list")
