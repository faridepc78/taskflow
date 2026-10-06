from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.cache import cache
from django.shortcuts import redirect, render

from ..forms import RegisterForm, VerifyEmailForm
from ..models import Profile
from ..services import OTP_MAX_ATTEMPTS, OTP_TIMEOUT, send_registration_otp


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
