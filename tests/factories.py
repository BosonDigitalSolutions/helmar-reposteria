import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"persona{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = "Ana"
    last_name = "Pérez"
    role = User.Role.VENTAS

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or "clave-segura-123")
        if create:
            obj.save()
