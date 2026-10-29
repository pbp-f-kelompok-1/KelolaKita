from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from accounts.models import Profile


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        input_class = (
            "block w-full min-w-0 rounded-xl border border-[#dfe5e0] bg-white "
            "px-4 py-3 text-sm text-[#1a2e1c] placeholder:text-[#78907c] "
            "outline-none transition focus:border-[#2e7d32] focus:ring-2 "
            "focus:ring-[#2e7d32]/20"
        )
        field_attrs = {
            "username": ("username", "Pilih nama pengguna"),
            "first_name": ("given-name", "Nama depan"),
            "last_name": ("family-name", "Nama belakang"),
            "email": ("email", "nama@email.com"),
            "password1": ("new-password", "Buat kata sandi"),
            "password2": ("new-password", "Ulangi kata sandi"),
        }
        for name, (autocomplete, placeholder) in field_attrs.items():
            self.fields[name].widget.attrs.update(
                {
                    "class": input_class,
                    "placeholder": placeholder,
                    "autocomplete": autocomplete,
                }
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        input_class = (
            "block w-full min-w-0 rounded-xl border border-[#dfe5e0] bg-white "
            "px-4 py-3 text-sm text-[#1a2e1c] placeholder:text-[#78907c] "
            "outline-none transition focus:border-[#2e7d32] focus:ring-2 "
            "focus:ring-[#2e7d32]/20"
        )
        self.fields["username"].widget.attrs.update(
            {
                "class": input_class,
                "placeholder": "Nama pengguna",
                "autocomplete": "username",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": input_class,
                "placeholder": "Kata sandi",
                "autocomplete": "current-password",
            }
        )
        self.fields["remember_me"].widget.attrs.update(
            {
                "class": (
                    "size-4 shrink-0 rounded border-[#b8c9bb] text-[#2e7d32] "
                    "focus:ring-2 focus:ring-[#2e7d32]/30"
                ),
            }
        )


class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True, label="Nama depan")
    last_name = forms.CharField(max_length=150, required=True, label="Nama belakang")
    email = forms.EmailField(required=True, label="Alamat email")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Email ini sudah digunakan oleh akun lain.")

        return email


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("phone_number", "address", "avatar_url")
        widgets = {
            "phone_number": forms.TextInput(
                attrs={"autocomplete": "tel", "placeholder": "Nomor telepon"}
            ),
            "address": forms.Textarea(
                attrs={"autocomplete": "street-address", "rows": 3}
            ),
            "avatar_url": forms.URLInput(
                attrs={"placeholder": "URL foto profil", "inputmode": "url"}
            ),
        }
