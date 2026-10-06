from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_otp_email_task(email, otp):
    send_mail(
        subject="Verify your email",
        message=f"Your verification code is: {otp}",
        from_email=None,
        recipient_list=[email],
    )


@shared_task
def send_password_reset_otp_email_task(email, otp):
    send_mail(
        subject="Reset your TaskFlow password",
        message=f"Your password reset code is: {otp}",
        from_email=None,
        recipient_list=[email],
    )
