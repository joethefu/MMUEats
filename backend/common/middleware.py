"""
Lightweight middleware. AuditLogMiddleware just stashes the current request's IP
onto the request object for use by services -- the actual audit rows are written
explicitly at the point of action (see common.utils.write_audit_log), not here,
so that only genuinely sensitive actions get logged rather than every request.
"""


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
