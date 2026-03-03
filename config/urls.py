from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve

from apps.academies.views import AcceptInvitationView, BrandedSignupView

urlpatterns = [
    path("admin/", admin.site.urls),
    # App routes
    path("", include("apps.dashboards.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("academy/", include("apps.academies.urls")),
    path("courses/", include("apps.courses.urls")),
    path("enrollments/", include("apps.enrollments.urls")),
    path("schedule/", include("apps.scheduling.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("tinymce/", include("tinymce.urls")),
    # Invitation acceptance (top-level for clean URLs)
    path("invitation/<str:token>/accept/", AcceptInvitationView.as_view(), name="accept-invitation"),
    path("join/<slug:slug>/", BrandedSignupView.as_view(), name="branded-signup"),
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
