from typing import cast

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from ..forms import ChangePasswordForm


@login_required
def change_password(request):
    user = cast(User, request.user)

    if request.method == "POST":
        form = ChangePasswordForm(request.POST)

        if form.is_valid():
            current_password = form.cleaned_data["current_password"]
            new_password = form.cleaned_data["new_password"]

            if not user.check_password(current_password):
                form.add_error(
                    "current_password",
                    "Current password is incorrect.",
                )
            else:
                try:
                    validate_password(
                        new_password,
                        user,
                    )
                except ValidationError as errors:
                    form.add_error(
                        "new_password",
                        errors,
                    )

                if not form.errors:
                    user.set_password(new_password)
                    user.save(update_fields=["password"])

                    update_session_auth_hash(
                        request,
                        user,
                    )

                    messages.success(
                        request,
                        "Your password has been changed successfully.",
                    )

                    return redirect("projects:dashboard")
    else:
        form = ChangePasswordForm()

    return render(
        request,
        "accounts/change_password.html",
        {"form": form},
    )
