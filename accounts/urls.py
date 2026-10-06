from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("verify-email/", views.verify_email, name="verify-email"),
    path(
        "resend-verification-code/",
        views.resend_registration_otp,
        name="resend-verification-code",
    ),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path(
        "forgot-password/",
        views.forgot_password,
        name="forgot-password",
    ),
    path(
        "verify-password-reset/",
        views.verify_password_reset,
        name="verify-password-reset",
    ),
    path(
        "resend-password-reset-code/",
        views.resend_password_reset_otp,
        name="resend-password-reset-code",
    ),
    path(
        "reset-password/",
        views.reset_password,
        name="reset-password",
    ),
    path(
        "change-password/",
        views.change_password,
        name="change-password",
    ),
]
