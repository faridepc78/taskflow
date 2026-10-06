from typing import cast

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    ChangePasswordForm,
    ForgotPasswordForm,
    LoginForm,
    RegisterForm,
    ResetPasswordForm,
    VerifyEmailForm,
    VerifyPasswordResetForm,
)
from .models import Profile
from .services import (
    OTP_MAX_ATTEMPTS,
    OTP_TIMEOUT,
    send_password_reset_otp,
    send_registration_otp,
)


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            request.session["pending_registration"] = {
                "first_name": form.cleaned_data["first_name"],
                "last_name": form.cleaned_data["last_name"],
                "username": form.cleaned_data["username"],
                "email": form.cleaned_data["email"],
                "password": make_password(form.cleaned_data["password"]),
            }

            send_registration_otp(form.cleaned_data["email"])

            return redirect("accounts:verify-email")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def verify_email(request):
    pending = request.session.get("pending_registration")

    if not pending:
        return redirect("accounts:register")

    email = pending["email"]
    otp_key = f"register_otp:{email}"
    attempts_key = f"register_otp_attempts:{email}"
    cooldown_key = f"register_otp_cooldown:{email}"

    cached_otp = cache.get(otp_key)

    if request.method == "POST":
        form = VerifyEmailForm(request.POST)

        if form.is_valid():
            code = form.cleaned_data["code"]

            if cached_otp is None:
                form.add_error("code", "Verification code has expired.")

            elif code != cached_otp:
                attempts = cache.get(attempts_key, 0) + 1

                cache.set(attempts_key, attempts, timeout=OTP_TIMEOUT)

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
                user = User(
                    first_name=pending["first_name"],
                    last_name=pending["last_name"],
                    username=pending["username"],
                    email=pending["email"],
                    password=pending["password"],
                )
                user.save()

                Profile.objects.create(user=user)

                cache.delete(otp_key)
                cache.delete(attempts_key)
                cache.delete(cooldown_key)

                del request.session["pending_registration"]

                messages.success(
                    request,
                    "Account created successfully. You can now log in.",
                )

                return redirect("accounts:login")

    else:
        form = VerifyEmailForm()

    return render(request, "accounts/verify_email.html", {"form": form})


def resend_registration_otp(request):
    if request.method != "POST":
        return redirect("accounts:verify-email")

    pending = request.session.get("pending_registration")

    if not pending:
        return redirect("accounts:register")

    email = pending["email"]

    cooldown_key = f"register_otp_cooldown:{email}"

    if cache.get(cooldown_key):
        messages.error(request, "Please wait before requesting another code.")
        return redirect("accounts:verify-email")

    send_registration_otp(email)

    messages.success(request, "A new verification code has been sent.")

    return redirect("accounts:verify-email")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("projects:dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
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

            elif code != cached_otp:
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

    if not email or not is_verified:
        return redirect("accounts:forgot-password")

    user = User.objects.filter(email__iexact=email).first()

    if user is None:
        request.session.pop("password_reset_email", None)
        request.session.pop("password_reset_verified", None)

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
