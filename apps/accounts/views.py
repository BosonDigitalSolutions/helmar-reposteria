from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView


class StaffAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"autocomplete": "username", "autofocus": True}
        )
        self.fields["password"].widget.attrs.update(
            {"autocomplete": "current-password"}
        )


class StaffLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = StaffAuthenticationForm
    redirect_authenticated_user = True


class StaffLogoutView(LogoutView):
    """El cierre de sesión solo acepta POST."""
