from django.urls import path

from .views import (
    ExpenseCreateView,
    ExpenseDeleteView,
    ExpenseListView,
    ExpenseUpdateView,
    IngredientCreateView,
    IngredientListView,
    IngredientUpdateView,
    InvestmentCreateView,
    InvestmentDeleteView,
    InvestmentListView,
    InvestmentUpdateView,
    MovementCreateView,
)

app_name = "inventory"

urlpatterns = [
    path("", IngredientListView.as_view(), name="ingredient_list"),
    path("nuevo/", IngredientCreateView.as_view(), name="ingredient_create"),
    path("<int:pk>/", IngredientUpdateView.as_view(), name="ingredient_update"),
    path("<int:pk>/movimiento/", MovementCreateView.as_view(), name="movement_create"),
    path("gastos/", ExpenseListView.as_view(), name="expense_list"),
    path("gastos/nuevo/", ExpenseCreateView.as_view(), name="expense_create"),
    path("gastos/<int:pk>/", ExpenseUpdateView.as_view(), name="expense_update"),
    path("gastos/<int:pk>/eliminar/", ExpenseDeleteView.as_view(), name="expense_delete"),
    path("inversiones/", InvestmentListView.as_view(), name="investment_list"),
    path("inversiones/nueva/", InvestmentCreateView.as_view(), name="investment_create"),
    path("inversiones/<int:pk>/", InvestmentUpdateView.as_view(), name="investment_update"),
    path("inversiones/<int:pk>/eliminar/", InvestmentDeleteView.as_view(), name="investment_delete"),
]
