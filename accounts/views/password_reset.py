from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.utils.crypto import constant_time_compare
from django.views.decorators.http import require_POST

from ..forms import ForgotPasswordForm, ResetPasswordForm, VerifyPasswordResetForm
from ..services import (
    OTP_MAX_ATTEMPTS,
    OTP_TIMEOUT,
    send_password_reset_otp,
)


def forgot_password(request):
    if request.user.is_authenticated:
        return redirect("projects:dashboard")

    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"].lower()

            user = User.objects.filter(email__iexact=email).first()

            if user is None:
                form.add_error(
                    "email",
                    "No account was found with this email address.",
                )
            else:
                cooldown_key = f"password_reset_otp_cooldown:{user.email}"
                if cache.get(cooldown_key):
                    form.add_error("email", "Please wait before requesting another code.")
                else:
                    request.session.pop("password_reset_verified", None)
                    request.session.pop("password_reset_verified_email", None)
                    request.session["password_reset_email"] = user.email
                    send_password_reset_otp(user.email)
                    return redirect("accounts:verify-password-reset")

    else:
        form = ForgotPasswordForm()

    return render(
        request,
        "accounts/forgot_password.html",
        {"form": form},
    )


def verify_password_reset(request):
    email = request.session.get("password_reset_email")

    if not email:
        return redirect("accounts:forgot-password")

    otp_key = f"password_reset_otp:{email}"
    attempts_key = f"password_reset_otp_attempts:{email}"
    cooldown_key = f"password_reset_otp_cooldown:{email}"

    cached_otp = cache.get(otp_key)

    if request.method == "POST":
        form = VerifyPasswordResetForm(request.POST)

        if form.is_valid():
            code = form.cleaned_data["code"]

            if cached_otp is None:
                form.add_error(
                    "code",
                    "Verification code has expired.",
                )

            elif not constant_time_compare(code, cached_otp):
                attempts = cache.get(attempts_key, 0) + 1

                cache.set(
                    attempts_key,
                    attempts,
                    timeout=OTP_TIMEOUT,
                )

                if attempts >= OTP_MAX_ATTEMPTS:
                    cache.delete(otp_key)
                    cache.delete(attempts_key)

                    form.add_error(
                        "code",
                        "Too many incorrect attempts. Please request a new code.",
                    )
                else:
                    remaining = OTP_MAX_ATTEMPTS - attempts

                    form.add_error(
                        "code",
                        f"Invalid verification code. {remaining} attempts remaining.",
                    )

            else:
                request.session["password_reset_verified"] = True
                request.session["password_reset_verified_email"] = email

                cache.delete(otp_key)
                cache.delete(attempts_key)
                cache.delete(cooldown_key)

                return redirect("accounts:reset-password")

    else:
        form = VerifyPasswordResetForm()

    return render(
        request,
        "accounts/verify_password_reset.html",
        {"form": form},
    )


@require_POST
def resend_password_reset_otp(request):
    email = request.session.get("password_reset_email")

    if not email:
        return redirect("accounts:forgot-password")

    cooldown_key = f"password_reset_otp_cooldown:{email}"

    if cache.get(cooldown_key):
        messages.error(
            request,
            "Please wait before requesting another code.",
        )

        return redirect("accounts:verify-password-reset")

    send_password_reset_otp(email)

    messages.success(
        request,
        "A new verification code has been sent.",
    )

    return redirect("accounts:verify-password-reset")


def reset_password(request):
    email = request.session.get("password_reset_email")
    is_verified = request.session.get("password_reset_verified")

    if not email or not is_verified or request.session.get("password_reset_verified_email") != email:
        return redirect("accounts:forgot-password")

    user = User.objects.filter(email__iexact=email).first()

    if user is None:
        request.session.pop("password_reset_email", None)
        request.session.pop("password_reset_verified", None)
        request.session.pop("password_reset_verified_email", None)

        return redirect("accounts:forgot-password")

    if request.method == "POST":
        form = ResetPasswordForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data["password"]

            try:
                validate_password(password, user)
            except ValidationError as errors:
                form.add_error("password", errors)

            if not form.errors:
                user.set_password(password)
                user.save(update_fields=["password"])

                request.session.pop("password_reset_email", None)
                request.session.pop("password_reset_verified", None)
                request.session.pop("password_reset_verified_email", None)

                messages.success(
                    request,
                    "Your password has been reset successfully.",
                )

                return redirect("accounts:login")
    else:
        form = ResetPasswordForm()

    return render(
        request,
        "accounts/reset_password.html",
        {"form": form},
    )
