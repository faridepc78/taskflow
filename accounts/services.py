import secrets

from django.core.cache import cache

from .tasks import (
    send_otp_email_task,
    send_password_reset_otp_email_task,
)

OTP_TIMEOUT = 300
OTP_COOLDOWN = 60
OTP_MAX_ATTEMPTS = 5


def generate_otp():
    return str(secrets.randbelow(900000) + 100000)


def send_registration_otp(email):
    otp = generate_otp()

    cache.set(f"register_otp:{email}", otp, timeout=OTP_TIMEOUT)

    cache.set(f"register_otp_attempts:{email}", 0, timeout=OTP_TIMEOUT)

    cache.set(f"register_otp_cooldown:{email}", True, timeout=OTP_COOLDOWN)

    send_otp_email_task.delay(email, otp)


def send_password_reset_otp(email):
    otp = generate_otp()

    cache.set(
        f"password_reset_otp:{email}",
        otp,
        timeout=OTP_TIMEOUT,
    )

    cache.set(
        f"password_reset_otp_attempts:{email}",
        0,
        timeout=OTP_TIMEOUT,
    )

    cache.set(
        f"password_reset_otp_cooldown:{email}",
        True,
        timeout=OTP_COOLDOWN,
    )

    send_password_reset_otp_email_task.delay(email, otp)
