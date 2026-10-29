from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.formats import date_format
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
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=user_profile)

        user_valid = user_form.is_valid()
        profile_valid = profile_form.is_valid()
        if user_valid and profile_valid:
            with transaction.atomic():
                user_form.save()
                profile_form.save()

            success_message = "Profil berhasil diperbarui."
            if is_ajax:
                return JsonResponse(
                    {
                        "success": True,
                        "message": success_message,
                        "full_name": request.user.get_full_name() or request.user.username,
                        "username": request.user.username,
                        "role": user_profile.get_role_display(),
                        "points": user_profile.points,
                        "avatar_url": user_profile.avatar_url,
                        "updated_at": user_profile.updated_at.isoformat(),
                        "updated_at_display": date_format(
                            timezone.localtime(user_profile.updated_at), "d F Y, H:i"
                        ),
                    }
                )

            messages.success(request, success_message)
            return redirect(request.path)

        if is_ajax:
            return JsonResponse(
                {
                    "success": False,
                    "errors": {
                        "user": {
                            name: list(errors)
                            for name, errors in user_form.errors.items()
                            if name != "__all__"
                        },
                        "profile": {
                            name: list(errors)
                            for name, errors in profile_form.errors.items()
                            if name != "__all__"
                        },
                    },
                    "non_field_errors": {
                        "user": list(user_form.non_field_errors()),
                        "profile": list(profile_form.non_field_errors()),
                    },
                },
                status=400,
            )
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
