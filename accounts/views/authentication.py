import hashlib

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..forms import LoginForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect("projects:dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)
        identifier_key = request.POST.get("username", "").strip().lower()
        client_ip = request.META.get("REMOTE_ADDR", "unknown")
        rate_key = "login_fail:" + hashlib.sha256(f"{client_ip}:{identifier_key}".encode()).hexdigest()
        blocked = cache.get(rate_key, 0) >= 10

        if form.is_valid():
            identifier = form.cleaned_data["username"]
            user = None if blocked else authenticate(
                request,
                username=identifier,
                password=form.cleaned_data["password"],
            )
            if not blocked and user is None and "@" in identifier:
                matches = User.objects.filter(email__iexact=identifier).values_list(
                    "username", flat=True
                )[:2]
                usernames = list(matches)
                if len(usernames) == 1:
                    user = authenticate(
                        request,
                        username=usernames[0],
                        password=form.cleaned_data["password"],
                    )

            if blocked or user is None:
                cache.add(rate_key, 0, timeout=900)
                try:
                    cache.incr(rate_key)
                except ValueError:
                    cache.set(rate_key, 1, timeout=900)
                form.add_error(
                    None,
                    "Too many login attempts. Please try again later." if blocked else "Invalid username or password.",
                )
            else:
                cache.delete(rate_key)
                login(request, user)

                return redirect("projects:dashboard")
    else:
        form = LoginForm()

    return render(
        request,
        "accounts/login.html",
        {"form": form},
    )


@require_POST
def logout_view(request):
    logout(request)

    return redirect("accounts:login")
