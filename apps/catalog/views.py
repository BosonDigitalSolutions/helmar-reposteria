from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.accounts.mixins import StaffPermissionMixin
from apps.catalog.models import Category

from .forms import CustomizationFormSet, PresentationFormSet, ProductForm
from .models import Product, ProductImage


class ProductQueryMixin:
    def filtered_products(self):
        query = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("categoria", "").strip()
        products = Product.objects.select_related("category")
        if query:
            products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query))
        if category:
            products = products.filter(category__slug=category)
        return products


class ProductListView(StaffPermissionMixin, ProductQueryMixin, ListView):
    permission_required = "catalog.view_product"
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        return self.filtered_products()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["filters"] = params.urlencode()
        context["all_categories"] = Category.objects.all()
        return context


class ProductFormMixin(StaffPermissionMixin):
    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = self.object or Product()
        data = self.request.POST or None
        context["presentations"] = PresentationFormSet(
            data,
            instance=instance,
            prefix="presentations",
        )
        context["options"] = CustomizationFormSet(
            data,
            instance=instance,
            prefix="options",
        )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        presentations = context["presentations"]
        options = context["options"]
        if not presentations.is_valid() or not options.is_valid():
            return self.form_invalid(form)
        with transaction.atomic():
            self.object = form.save()
            presentations.instance = self.object
            options.instance = self.object
            presentations.save()
            options.save()
            image = form.cleaned_data.get("new_image")
            if image:
                ProductImage.objects.create(
                    product=self.object,
                    image=image,
                    alt_text=self.object.name,
                )
            delete_ids = self.request.POST.getlist("delete_image")
            if delete_ids:
                ProductImage.objects.filter(product=self.object, pk__in=delete_ids).delete()
        messages.success(self.request, "El producto se guardó.")
        return redirect(self.success_url)


class ProductCreateView(ProductFormMixin, CreateView):
    permission_required = "catalog.add_product"

    def get_context_data(self, **kwargs):
        self.object = None
        return super().get_context_data(**kwargs)


class ProductUpdateView(ProductFormMixin, UpdateView):
    permission_required = "catalog.change_product"


class ProductDeleteView(StaffPermissionMixin, DeleteView):
    permission_required = "catalog.delete_product"
    model = Product
    template_name = "components/confirm_delete.html"
    success_url = reverse_lazy("catalog:product_list")

    def form_valid(self, form):
        messages.success(self.request, "El producto se eliminó.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("catalog:product_list")
        context["object_label"] = self.object.name
        return context
