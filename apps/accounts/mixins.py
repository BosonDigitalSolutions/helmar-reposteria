from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)

from .roles import ROLE_GROUP_NAMES


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige sesión y un grupo de rol real, no solo un botón oculto."""

    def test_func(self) -> bool:
        user = self.request.user
        if user.is_superuser:
            return True
        return user.groups.filter(name__in=ROLE_GROUP_NAMES.values()).exists()


class StaffPermissionMixin(RoleRequiredMixin, PermissionRequiredMixin):
    """Exige un rol interno y el permiso concreto de Django."""
