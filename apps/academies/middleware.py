class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.academy = None
        if hasattr(request, "user") and request.user.is_authenticated:
            request.academy = request.user.current_academy
        response = self.get_response(request)
        return response
