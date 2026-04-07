from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm


class CaseInsensitiveAuthenticationForm(AuthenticationForm):
    """Authenticate username case-insensitively for admin login."""

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:
            user_model = get_user_model()
            matched_user = user_model.objects.filter(username__iexact=username).first()
            auth_username = matched_user.get_username() if matched_user else username

            self.user_cache = authenticate(
                self.request,
                username=auth_username,
                password=password,
            )

            if self.user_cache is None:
                raise self.get_invalid_login_error()

            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data