from django.db import migrations


CATEGORIES = [
    ("Pasteles personalizados", "pasteles-personalizados", 1),
    ("Galletas personalizadas", "galletas-personalizadas", 2),
    ("Cupcakes", "cupcakes", 3),
    ("Cajas de regalo", "cajas-de-regalo", 4),
    ("Postres individuales", "postres-individuales", 5),
    ("Eventos especiales", "eventos-especiales", 6),
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    for name, slug, display_order in CATEGORIES:
        Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "display_order": display_order},
        )


def remove_seed_categories(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Category.objects.filter(slug__in=[slug for _name, slug, _order in CATEGORIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, remove_seed_categories),
    ]
