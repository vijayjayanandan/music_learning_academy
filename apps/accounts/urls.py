from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileEditView.as_view(), name="profile-edit"),
    path(
        "switch-academy/<slug:slug>/",
        views.SwitchAcademyView.as_view(),
        name="switch-academy",
    ),
    # Password reset (rate-limited)
    path(
        "password-reset/",
        views.RateLimitedPasswordResetView.as_view(),
        name="password-reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password-reset-done",
    ),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("password-reset-complete"),
        ),
        name="password-reset-confirm",
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password-reset-complete",
    ),
    # Email verification
    path(
        "verify-email/<uidb64>/<token>/",
        views.VerifyEmailView.as_view(),
        name="verify-email",
    ),
    path(
        "verify-email/resend/",
        views.ResendVerificationView.as_view(),
        name="resend-verification",
    ),
    # Parent portal
    path(
        "parent-dashboard/",
        views.ParentDashboardView.as_view(),
        name="parent-dashboard",
    ),
    path("link-child/", views.LinkChildView.as_view(), name="link-child"),
    # GDPR: Data export & account deletion
    path("data-export/", views.DataExportView.as_view(), name="data-export"),
    path("delete-account/", views.AccountDeleteView.as_view(), name="account-delete"),
    # Parental consent
    path(
        "parental-consent/<str:token>/approve/",
        views.ApproveParentalConsentView.as_view(),
        name="approve-parental-consent",
    ),
]
