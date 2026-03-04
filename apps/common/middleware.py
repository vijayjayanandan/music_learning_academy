import uuid

from django.http import HttpResponse
from django.template.loader import render_to_string


class RatelimitMiddleware:
    """Convert django-ratelimit's Ratelimited exception into a 429 response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        from django_ratelimit.exceptions import Ratelimited

        if isinstance(exception, Ratelimited):
            try:
                html = render_to_string("429.html", request=request)
            except Exception:
                html = "<h1>429 Too Many Requests</h1><p>Please slow down and try again later.</p>"
            return HttpResponse(html, status=429)
        return None


class SecurityHeadersMiddleware:
    """Add security headers not covered by Django's SecurityMiddleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = (
            "camera=(), microphone=(self), geolocation=(), payment=()"
        )
        return response


class RequestIDMiddleware:
    """Attach a unique request ID for structured logging and tracing."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import logging
        request_id = request.META.get("HTTP_X_REQUEST_ID", str(uuid.uuid4()))
        request.request_id = request_id
        # Make request_id available in log records via a filter
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id
            return record

        logging.setLogRecordFactory(record_factory)
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        # Restore original factory
        logging.setLogRecordFactory(old_factory)
        return response
