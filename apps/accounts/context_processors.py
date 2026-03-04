import os


def social_login_context(request):
    """Provide flags indicating which social login providers are configured."""
    return {
        "social_google_enabled": bool(os.environ.get("GOOGLE_OAUTH_CLIENT_ID")),
        "social_facebook_enabled": bool(os.environ.get("FACEBOOK_APP_ID")),
    }
