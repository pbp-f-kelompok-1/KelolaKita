from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nama depan",
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nama belakang",
    )
    email = forms.EmailField(
        required=True,
        label="Alamat email",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Email ini sudah digunakan oleh akun lain."
            )

        return email


class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(
        required=False,
        label="Ingat saya",
    )