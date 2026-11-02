from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "authentication"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    path("verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path("resend-verification/", views.ResendVerificationView.as_view(), name="resend-verification"),

    path("password-reset/request/", views.PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/confirm/", views.PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
]
