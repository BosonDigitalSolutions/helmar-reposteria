from django.contrib import admin

from .models import Expense, Ingredient, Investment, StockMovement


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "stock_quantity", "average_unit_cost", "reorder_level")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "kind", "quantity", "amount", "occurred_on")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("category", "amount", "occurred_on")


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ("name", "amount", "acquired_on")
