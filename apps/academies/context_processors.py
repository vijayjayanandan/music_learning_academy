def academy_context(request):
    context = {
        "current_academy": getattr(request, "academy", None),
    }
    if hasattr(request, "user") and request.user.is_authenticated:
        academy = getattr(request, "academy", None)
        if academy:
            context["user_role"] = request.user.get_role_in(academy)
            context["user_academies"] = request.user.get_academies()
    return context
