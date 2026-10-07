from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string


@shared_task
def send_otp_email_task(email, otp):
    send_mail(
        subject="Verify your email",
        message=f"Your verification code is: {otp}",
        from_email=None,
        recipient_list=[email],
        html_message=render_to_string(
            "emails/verification.html",
            {"otp": otp},
        ),
    )


@shared_task
def send_password_reset_otp_email_task(email, otp):
    send_mail(
        subject="Reset your TaskFlow password",
        message=f"Your password reset code is: {otp}",
        from_email=None,
        recipient_list=[email],
        html_message=render_to_string(
            "emails/password_reset.html",
            {"otp": otp},
        ),
    )
