"""Shared helpers used across apps."""

import secrets


def generate_secure_token(nbytes: int = 32) -> str:
    """Cryptographically secure, URL-safe token for email verification / password reset."""
    return secrets.token_urlsafe(nbytes)


def mask_token(token: str) -> str:
    """Never log a full token — only show enough to correlate log lines, e.g. 'aB3f...9kLp'."""
    if not token or len(token) < 8:
        return "****"
    return f"{token[:4]}...{token[-4:]}"


def write_audit_log(actor, action, obj=None, metadata=None, request=None):
    """Create an AuditLog row. Call this from any view/service performing a sensitive action."""
    from common.models import AuditLog

    ip = None
    if request is not None:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")

    AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        object_type=obj.__class__.__name__ if obj is not None else "",
        object_id=str(getattr(obj, "pk", "")) if obj is not None else "",
        metadata=metadata or {},
        ip_address=ip,
    )


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")
