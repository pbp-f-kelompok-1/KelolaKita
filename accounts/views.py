from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.forms import LoginForm, RegisterForm


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