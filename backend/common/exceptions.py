"""
Consistent API error envelope for every error type (validation, auth, 404, 500, etc).

Response shape:
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Human-readable summary",
    "details": {...}   # field-level errors when applicable
  }
}

Raw stack traces are never returned to the client.
"""

import logging

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import status

logger = logging.getLogger("django")

_CODE_BY_STATUS = {
    400: "validation_error",
    401: "authentication_error",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    429: "throttled",
    500: "server_error",
}


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is not None:
        code = _CODE_BY_STATUS.get(response.status_code, "error")
        detail = response.data

        if isinstance(detail, dict) and "detail" in detail and len(detail) == 1:
            raw = detail["detail"]
            # Serializer-level ValidationError({"detail": ...}, code=...) gets
            # re-wrapped by DRF into {"detail": [ErrorDetail(...)]} as it bubbles
            # up through run_validation/is_valid — unwrap the single-item list so
            # we can read both the message and the original custom `code`.
            if isinstance(raw, list) and len(raw) == 1:
                raw = raw[0]
            message = str(raw)
            details = None
            # DRF preserves a per-error `code` on ErrorDetail (e.g. our serializers
            # raise ValidationError(..., code="email_not_verified")) — surface that
            # specific code to the client instead of the generic status-based one
            # whenever the view set something more precise than "invalid".
            detail_code = getattr(raw, "code", None)
            if detail_code and detail_code not in ("invalid",):
                code = detail_code
        elif isinstance(detail, (list, dict)):
            message = "One or more fields are invalid." if response.status_code == 400 else "Request failed."
            details = detail
        else:
            message = str(detail)
            details = None

        response.data = {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                **({"details": details} if details else {}),
            },
        }
        return response

    # Unhandled exception -> never leak internals, but do log server-side.
    logger.exception("Unhandled server error", exc_info=exc)
    from rest_framework.response import Response

    return Response(
        {
            "success": False,
            "error": {
                "code": "server_error",
                "message": "Something went wrong. Please try again shortly.",
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
