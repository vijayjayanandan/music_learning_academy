import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.views.static import serve

from apps.academies.views import AcceptInvitationView, BrandedSignupView
from apps.common.views import health_check, health_check_detail, robots_txt

ADMIN_URL_PATH = os.environ.get("ADMIN_URL_PATH", "manage-internal/")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("health/detail/", health_check_detail, name="health-check-detail"),
    path(ADMIN_URL_PATH, admin.site.urls),
    # App routes
    path("", include("apps.dashboards.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("accounts/social/", include("allauth.socialaccount.urls")),
    path("accounts/social/", include("allauth.socialaccount.providers.google.urls")),
    path("accounts/social/", include("allauth.socialaccount.providers.facebook.urls")),
    path("academy/", include("apps.academies.urls")),
    path("courses/", include("apps.courses.urls")),
    path("enrollments/", include("apps.enrollments.urls")),
    path("schedule/", include("apps.scheduling.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("practice/", include("apps.practice.urls")),
    path("payments/", include("apps.payments.urls")),
    path("tools/", include("apps.music_tools.urls")),
    path("library/", include("apps.library.urls")),
    path("tinymce/", include("tinymce.urls")),
    # Invitation acceptance (top-level for clean URLs)
    path("invitation/<str:token>/accept/", AcceptInvitationView.as_view(), name="accept-invitation"),
    path("join/<slug:slug>/", BrandedSignupView.as_view(), name="branded-signup"),
    # Legal pages
    path("terms/", TemplateView.as_view(template_name="legal/terms.html"), name="terms"),
    path("privacy/", TemplateView.as_view(template_name="legal/privacy.html"), name="privacy"),
    # SEO
    path("robots.txt", robots_txt, name="robots-txt"),
    # Favicon
    path("favicon.ico", serve, {"document_root": settings.STATICFILES_DIRS[0], "path": "favicon.ico"}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
