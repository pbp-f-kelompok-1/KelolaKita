from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.forms import LoginForm, ProfileUpdateForm, RegisterForm, UserUpdateForm
from accounts.models import Profile


def get_safe_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next")

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    return None


def register(request):
    if request.user.is_authenticated:
        return redirect("landing_page")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            auth_login(request, user)

            messages.success(
                request,
                "Akun berhasil dibuat. Selamat datang di KelolaKita!",
            )
            return redirect("landing_page")
    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


def login_user(request):
    if request.user.is_authenticated:
        return redirect("landing_page")

    if request.method == "POST":
        form = LoginForm(request=request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)

            if form.cleaned_data["remember_me"]:
                request.session.set_expiry(60 * 60 * 24 * 14)
            else:
                request.session.set_expiry(0)

            messages.success(
                request,
                f"Selamat datang kembali, {user.first_name or user.username}!",
            )

            return redirect(get_safe_next_url(request) or "landing_page")
    else:
        form = LoginForm(request=request)

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "next": get_safe_next_url(request) or "",
        },
    )


@require_POST
def logout_user(request):
    auth_logout(request)
    messages.success(request, "Kamu berhasil keluar dari akun.")
    return redirect("landing_page")


@login_required
def profile(request):
    user_profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=user_profile)

        user_valid = user_form.is_valid()
        profile_valid = profile_form.is_valid()
        if user_valid and profile_valid:
            with transaction.atomic():
                user_form.save()
                profile_form.save()

            messages.success(request, "Profil berhasil diperbarui.")
            return redirect(request.path)
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=user_profile)

    return render(
        request,
        "accounts/profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "profile": user_profile,
        },
    )
