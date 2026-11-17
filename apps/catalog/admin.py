from django.contrib import admin

from .models import Category, Product, ProductCustomization, ProductImage, ProductPresentation


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductPresentationInline(admin.TabularInline):
    model = ProductPresentation
    extra = 0


class ProductCustomizationInline(admin.TabularInline):
    model = ProductCustomization
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "display_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price_mode", "is_active", "is_customizable")
    list_filter = ("category", "price_mode", "is_active", "is_customizable")
    search_fields = ("name", "sku")
    inlines = [ProductImageInline, ProductPresentationInline, ProductCustomizationInline]
