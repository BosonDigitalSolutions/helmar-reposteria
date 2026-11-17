"""Datos del catálogo público."""

from .models import Category, Product


def public_catalog() -> tuple[list[dict], list[Category]]:
    categories = list(Category.objects.all())
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images", "presentations", "customizations")
    )
    payload = []
    for product in products:
        image = next(iter(product.images.all()), None)
        payload.append(
            {
                "id": product.pk,
                "name": product.name,
                "category": product.category.slug,
                "category_name": product.category.name,
                "description": product.description,
                "image": image.image.url if image else "",
                "price_label": product.price_label,
                "customizable": product.is_customizable,
                "presentations": [item.name for item in product.presentations.all()],
                "customizations": [item.name for item in product.customizations.all()],
            }
        )
    return payload, categories
