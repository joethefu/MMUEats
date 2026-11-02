"""
Email-sending Celery tasks for the auth flow.

CELERY_TASK_ALWAYS_EAGER=True in dev means these run synchronously in-process
(no Redis worker required to develop locally); in production they're queued
through Celery + Redis as configured in settings.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail

from common.utils import mask_token

logger = logging.getLogger("django")


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_verification_email(self, user_email, full_name, token):
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "Verify your MMUEats email address"

    # Plain-text fallback for email clients that don't render HTML
    text_body = (
        f"Hi {full_name},\n\n"
        f"Welcome to MMUEats! Click the Verify button to activate your account.:\n\n"
        f"{verify_url}\n\n"
        f"This link expires in {settings.EMAIL_VERIFICATION_TOKEN_LIFETIME_HOURS} hours.\n\n"
        f"If you didn't create this account, you can safely ignore this email.\n\n"
        f"— MMUEats"
    )

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0; padding: 24px;">
        <h2 style="color: #1a1a1a;">Welcome to MMUEats, {full_name}!</h2>
        <p style="color: #444; font-size: 15px; line-height: 1.5;">
            Click the Verify button to activate your account.
        </p>
        <div style="text-align: center; margin: 32px 0;">
            <a href="{verify_url}"
               style="background-color: #e67e22; color: #ffffff; text-decoration: none;
                      padding: 14px 36px; border-radius: 6px; font-size: 16px;
                      font-weight: bold; display: inline-block;">
                Verify
            </a>
        </div>
        <p style="color: #888; font-size: 13px;">
            This link expires in {settings.EMAIL_VERIFICATION_TOKEN_LIFETIME_HOURS} hours.
            If you didn't create this account, you can safely ignore this email.
        </p>
        <p style="color: #888; font-size: 13px;">— MMUEats</p>
    </div>
    """

    try:
        email = EmailMultiAlternatives(
            subject, text_body, settings.DEFAULT_FROM_EMAIL, [user_email])
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
        logger.info("Verification email queued for %s (token=%s)",
                    user_email, mask_token(token))
    except Exception as exc:
        logger.warning(
            "Failed to send verification email to %s: %s", user_email, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset_email(self, user_email, full_name, token):
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    subject = "Reset your MMUEats password"

    text_body = (
        f"Hi {full_name},\n\n"
        f"We received a request to reset your MMUEats password. Click the link below:\n\n"
        f"{reset_url}\n\n"
        f"This link expires in {settings.PASSWORD_RESET_TOKEN_LIFETIME_HOURS} hour(s). "
        f"If you didn't request this, you can safely ignore this email — your password won't change.\n\n"
        f"— MMUEats"
    )

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0; padding: 24px;">
        <h2 style="color: #1a1a1a;">Reset your password</h2>
        <p style="color: #444; font-size: 15px; line-height: 1.5;">
            Hi {full_name}, we received a request to reset your MMUEats password.
        </p>
        <div style="text-align: center; margin: 32px 0;">
            <a href="{reset_url}"
               style="background-color: #e67e22; color: #ffffff; text-decoration: none;
                      padding: 14px 36px; border-radius: 6px; font-size: 16px;
                      font-weight: bold; display: inline-block;">
                Reset Password
            </a>
        </div>
        <p style="color: #888; font-size: 13px;">
            This link expires in {settings.PASSWORD_RESET_TOKEN_LIFETIME_HOURS} hour(s).
            If you didn't request this, you can safely ignore this email — your password won't change.
        </p>
        <p style="color: #888; font-size: 13px;">— MMUEats</p>
    </div>
    """

    try:
        email = EmailMultiAlternatives(
            subject, text_body, settings.DEFAULT_FROM_EMAIL, [user_email])
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
        logger.info("Password reset email queued for %s (token=%s)",
                    user_email, mask_token(token))
    except Exception as exc:
        logger.warning(
            "Failed to send password reset email to %s: %s", user_email, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_partner_approved_email(self, user_email, full_name, role_label, token):
    from django.core.mail import EmailMultiAlternatives

    set_password_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    subject = f"You're approved as a {role_label} on MMUEats!"
    hours = settings.PASSWORD_RESET_TOKEN_LIFETIME_HOURS

    text_body = (
        f"Hi {full_name},\n\n"
        f"Great news — your application to join MMUEats as a {role_label} has been approved.\n\n"
        f"Set your account password to get started:\n\n{set_password_url}\n\n"
        f"This link expires in {hours} hour(s); request a new one from the login page's "
        f"'Forgot password' link if it expires.\n\n— MMUEats"
    )
    html_body = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:480px;margin:0;padding:24px;color:#1e293b;">
      <h2 style="margin:0 0 16px;color:#7b1e2b;">You're approved! 🎉</h2>
      <p>Hi {full_name},</p>
      <p>Great news — your application to join MMUEats as a <strong>{role_label}</strong> has been approved.</p>
      <p>Set your account password to get started:</p>
      <p style="margin:28px 0;">
        <a href="{set_password_url}"
           style="background-color:#e67e22;color:#ffffff;text-decoration:none;font-weight:bold;
                  padding:12px 28px;border-radius:6px;display:inline-block;">Set Password</a>
      </p>
      <p style="font-size:13px;color:#64748b;">This link expires in {hours} hour(s). If it expires, use
      “Forgot password” on the login page to get a new one.</p>
      <p style="font-size:13px;color:#64748b;">— MMUEats</p>
    </div>
    """
    try:
        msg = EmailMultiAlternatives(
            subject, text_body, settings.DEFAULT_FROM_EMAIL, [user_email])
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info("Partner-approved email sent to %s (token=%s)",
                    user_email, mask_token(token))
    except Exception as exc:
        logger.warning(
            "Failed to send partner-approved email to %s: %s", user_email, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_partner_rejected_email(self, user_email, full_name, role_label, notes):
    subject = f"Update on your MMUEats {role_label} application"
    message = (
        f"Hi {full_name},\n\n"
        f"Thanks for your interest in joining MMUEats as a {role_label}. After review, we're unable to "
        f"approve your application at this time"
        + (f":\n\n{notes}\n\n" if notes else ".\n\n")
        + "You're welcome to reach out to support if you have questions.\n\n— MMUEats"
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                  [user_email], fail_silently=False)
    except Exception as exc:
        logger.warning(
            "Failed to send partner-rejected email to %s: %s", user_email, exc)
        raise self.retry(exc=exc)
