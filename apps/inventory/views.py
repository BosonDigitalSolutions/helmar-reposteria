from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View

from apps.accounts.mixins import StaffPermissionMixin

from .forms import ExpenseForm, IngredientForm, InvestmentForm, MovementForm
from .models import Expense, Ingredient, Investment
from .services import record_movement


class IngredientListView(StaffPermissionMixin, ListView):
    permission_required = "inventory.view_ingredient"
    model = Ingredient
    template_name = "inventory/ingredient_list.html"
    context_object_name = "ingredients"


class IngredientCreateView(StaffPermissionMixin, CreateView):
    permission_required = "inventory.add_ingredient"
    model = Ingredient
    form_class = IngredientForm
    template_name = "inventory/ingredient_form.html"
    success_url = reverse_lazy("inventory:ingredient_list")

    def form_valid(self, form):
        messages.success(self.request, "El insumo quedó registrado. La existencia entra con una compra.")
        return super().form_valid(form)


class IngredientUpdateView(StaffPermissionMixin, UpdateView):
    permission_required = "inventory.change_ingredient"
    model = Ingredient
    form_class = IngredientForm
    template_name = "inventory/ingredient_form.html"
    success_url = reverse_lazy("inventory:ingredient_list")

    def form_valid(self, form):
        messages.success(self.request, "El insumo se actualizó.")
        return super().form_valid(form)


class MovementCreateView(StaffPermissionMixin, View):
    permission_required = "inventory.add_stockmovement"
    template_name = "inventory/movement_form.html"

    def get(self, request, pk):
        ingredient = get_object_or_404(Ingredient, pk=pk)
        return self._render(request, ingredient, MovementForm())

    def post(self, request, pk):
        ingredient = get_object_or_404(Ingredient, pk=pk)
        form = MovementForm(request.POST)
        if not form.is_valid():
            return self._render(request, ingredient, form)
        try:
            record_movement(
                ingredient,
                kind=form.cleaned_data["kind"],
                quantity=form.cleaned_data["quantity"],
                unit_cost=form.cleaned_data["unit_cost"],
                occurred_on=form.cleaned_data["occurred_on"],
                note=form.cleaned_data["note"],
            )
        except ValidationError as exc:
            if hasattr(exc, "error_dict"):
                for field, errors in exc.error_dict.items():
                    for error in errors:
                        form.add_error(field if field in form.fields else None, error)
            else:
                form.add_error(None, " ".join(exc.messages))
            return self._render(request, ingredient, form)
        messages.success(request, "El movimiento quedó registrado.")
        return redirect("inventory:movement_create", pk=ingredient.pk)

    def _render(self, request, ingredient, form):
        from django.shortcuts import render

        return render(
            request,
            self.template_name,
            {
                "ingredient": ingredient,
                "form": form,
                "movements": ingredient.movements.all()[:20],
            },
        )


class ExpenseListView(StaffPermissionMixin, ListView):
    permission_required = "inventory.view_expense"
    model = Expense
    template_name = "inventory/expense_list.html"
    context_object_name = "expenses"


class ExpenseCreateView(StaffPermissionMixin, CreateView):
    permission_required = "inventory.add_expense"
    model = Expense
    form_class = ExpenseForm
    template_name = "inventory/expense_form.html"
    success_url = reverse_lazy("inventory:expense_list")

    def form_valid(self, form):
        messages.success(self.request, "El gasto quedó registrado.")
        return super().form_valid(form)


class ExpenseUpdateView(StaffPermissionMixin, UpdateView):
    permission_required = "inventory.change_expense"
    model = Expense
    form_class = ExpenseForm
    template_name = "inventory/expense_form.html"
    success_url = reverse_lazy("inventory:expense_list")


class ExpenseDeleteView(StaffPermissionMixin, DeleteView):
    permission_required = "inventory.delete_expense"
    model = Expense
    template_name = "components/confirm_delete.html"
    success_url = reverse_lazy("inventory:expense_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_label"] = f"{self.object.get_category_display()} del {self.object.occurred_on}"
        context["cancel_url"] = reverse_lazy("inventory:expense_list")
        return context

    def form_valid(self, form):
        messages.success(self.request, "El gasto se eliminó.")
        return super().form_valid(form)


class InvestmentListView(StaffPermissionMixin, ListView):
    permission_required = "inventory.view_investment"
    model = Investment
    template_name = "inventory/investment_list.html"
    context_object_name = "investments"


class InvestmentCreateView(StaffPermissionMixin, CreateView):
    permission_required = "inventory.add_investment"
    model = Investment
    form_class = InvestmentForm
    template_name = "inventory/investment_form.html"
    success_url = reverse_lazy("inventory:investment_list")

    def form_valid(self, form):
        messages.success(self.request, "La inversión quedó registrada.")
        return super().form_valid(form)


class InvestmentUpdateView(StaffPermissionMixin, UpdateView):
    permission_required = "inventory.change_investment"
    model = Investment
    form_class = InvestmentForm
    template_name = "inventory/investment_form.html"
    success_url = reverse_lazy("inventory:investment_list")


class InvestmentDeleteView(StaffPermissionMixin, DeleteView):
    permission_required = "inventory.delete_investment"
    model = Investment
    template_name = "components/confirm_delete.html"
    success_url = reverse_lazy("inventory:investment_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_label"] = self.object.name
        context["cancel_url"] = reverse_lazy("inventory:investment_list")
        return context

    def form_valid(self, form):
        messages.success(self.request, "La inversión se eliminó.")
        return super().form_valid(form)
