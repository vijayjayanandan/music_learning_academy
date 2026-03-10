from .dev import *  # noqa: F401,F403

# Use MD5 for fast password hashing in tests (not secure, fine for tests)
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Use in-memory email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disable rate limiting in tests to avoid 429 responses
RATELIMIT_ENABLE = False

# Cron endpoint key for tests
CRON_API_KEY = "test-cron-secret-key"
