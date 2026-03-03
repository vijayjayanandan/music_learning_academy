def academy_context(request):
    context = {
        "current_academy": getattr(request, "academy", None),
    }
    if hasattr(request, "user") and request.user.is_authenticated:
        academy = getattr(request, "academy", None)
        if academy:
            context["user_role"] = request.user.get_role_in(academy)
            context["user_academies"] = request.user.get_academies()
            # Feature flags for template-level feature toggling
            context["academy_features"] = {
                key: academy.has_feature(key)
                for key in academy.DEFAULT_FEATURES
            }
    return context
