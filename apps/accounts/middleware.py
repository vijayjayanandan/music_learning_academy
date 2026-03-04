import zoneinfo
from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, "timezone"):
            user_tz = request.user.timezone
            if user_tz:
                try:
                    timezone.activate(zoneinfo.ZoneInfo(user_tz))
                except (KeyError, Exception):
                    timezone.deactivate()
            else:
                timezone.deactivate()
        else:
            timezone.deactivate()
        return self.get_response(request)
