import os  # noqa: E402

# Dev-only fallback so local development works without setting the env var
os.environ.setdefault(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-key-do-not-use-in-production",
)

from .base import *  # noqa: F401,F403

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Django Debug Toolbar
INSTALLED_APPS += ["debug_toolbar", "django_extensions"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]

# Email — use SendGrid if configured, otherwise console
# Set USE_CONSOLE_EMAIL=1 in .env to force console output during dev
if os.environ.get("USE_CONSOLE_EMAIL", ""):
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# Otherwise, inherits from base.py (SendGrid if API key present, else console)
