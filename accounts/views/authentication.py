from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..forms import LoginForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect("projects:dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            identifier = form.cleaned_data["username"]
            user = authenticate(
                request,
                username=identifier,
                password=form.cleaned_data["password"],
            )
            if user is None and "@" in identifier:
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

            if user is None:
                form.add_error(
                    None,
                    "Invalid username or password.",
                )
            else:
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
