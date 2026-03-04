import json

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView
from django_ratelimit.decorators import ratelimit

from apps.academies.models import Academy
from .forms import RegisterForm, ProfileForm
from .models import User
from .tokens import email_verification_token


def _send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    protocol = "https" if request.is_secure() else "http"
    domain = request.get_host()
    verify_url = f"{protocol}://{domain}/accounts/verify-email/{uid}/{token}/"
    html_message = render_to_string("emails/verification_email.html", {
        "user": user,
        "verify_url": verify_url,
    })
    plain_message = (
        f"Hi {user.first_name or 'there'},\n\n"
        f"Please verify your email address by visiting:\n{verify_url}\n\n"
        f"If you didn't create an account, you can ignore this email."
    )
    send_mail(
        "Verify your email - Music Learning Academy",
        plain_message,
        None,  # uses DEFAULT_FROM_EMAIL
        [user.email],
        html_message=html_message,
    )


@method_decorator(ratelimit(key="ip", rate="5/5m", method="POST", block=True), name="post")
class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("login")


@method_decorator(ratelimit(key="ip", rate="3/10m", method="POST", block=True), name="post")
class RegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        _send_verification_email(self.request, self.object)
        return response


class VerifyEmailView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and email_verification_token.check_token(user, token):
            user.email_verified = True
            user.save(update_fields=["email_verified"])
            messages.success(request, "Email verified successfully!")
            return redirect("dashboard")
        else:
            return render(request, "accounts/email_verification_invalid.html")


@method_decorator(ratelimit(key="ip", rate="2/10m", method="POST", block=True), name="post")
class ResendVerificationView(LoginRequiredMixin, View):
    def post(self, request):
        if not request.user.email_verified:
            _send_verification_email(request, request.user)
            if request.headers.get("HX-Request"):
                return render(request, "accounts/partials/_verification_resent.html")
            messages.success(request, "Verification email sent! Check your inbox.")
        return redirect("dashboard")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["memberships"] = self.request.user.memberships.select_related("academy").all()
        return ctx


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("profile")

    def get_object(self):
        return self.request.user


class SwitchAcademyView(LoginRequiredMixin, View):
    def post(self, request, slug):
        academy = get_object_or_404(Academy, slug=slug)
        if request.user.memberships.filter(academy=academy).exists():
            request.user.current_academy = academy
            request.user.save(update_fields=["current_academy"])
        return redirect("dashboard")


@method_decorator(ratelimit(key="ip", rate="3/10m", method="POST", block=True), name="post")
class RateLimitedPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.html"
    html_email_template_name = "emails/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("password-reset-done")


class ParentDashboardView(LoginRequiredMixin, View):
    """FEAT-032: Parent/guardian portal."""

    def get(self, request):
        children = request.user.children.all()
        children_data = []
        for child in children:
            from apps.enrollments.models import Enrollment
            from apps.practice.models import PracticeLog
            enrollments = Enrollment.objects.filter(student=child, status="active")
            recent_practice = PracticeLog.objects.filter(student=child).order_by("-date")[:5]
            children_data.append({
                "user": child,
                "enrollments": enrollments,
                "recent_practice": recent_practice,
            })
        return render(request, "accounts/parent_dashboard.html", {
            "children_data": children_data,
        })


class LinkChildView(LoginRequiredMixin, View):
    """Link a child account to parent.

    Security: Only links if the child account has no existing parent
    and the child is a student in at least one academy that the parent
    belongs to. This prevents arbitrary account linking.
    """

    def post(self, request):
        from django.contrib import messages as django_messages
        child_email = request.POST.get("child_email", "").strip()
        try:
            child = User.objects.get(email=child_email)
            # Security: prevent linking if child already has a parent
            if child.parent is not None:
                django_messages.error(request, "This account is already linked to a parent.")
                return redirect("parent-dashboard")
            # Security: prevent linking yourself
            if child == request.user:
                django_messages.error(request, "You cannot link your own account as a child.")
                return redirect("parent-dashboard")
            # Security: verify shared academy membership
            parent_academy_ids = set(
                request.user.memberships.values_list("academy_id", flat=True)
            )
            child_academy_ids = set(
                child.memberships.filter(role="student").values_list("academy_id", flat=True)
            )
            if not parent_academy_ids & child_academy_ids:
                django_messages.error(request, "No shared academy found with this student.")
                return redirect("parent-dashboard")
            child.parent = request.user
            child.save(update_fields=["parent"])
            request.user.is_parent = True
            request.user.save(update_fields=["is_parent"])
            django_messages.success(request, f"Successfully linked {child_email}.")
        except User.DoesNotExist:
            django_messages.error(request, "No account found with that email.")
        return redirect("parent-dashboard")


class DataExportView(LoginRequiredMixin, View):
    """GDPR: Export all user data as JSON."""

    def get(self, request):
        user = request.user
        from apps.enrollments.models import Enrollment
        from apps.practice.models import PracticeLog

        data = {
            "account": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "date_joined": user.date_joined.isoformat(),
                "timezone": str(getattr(user, "timezone", "")),
            },
            "memberships": list(
                user.memberships.select_related("academy").values(
                    "academy__name", "role", "created_at",
                )
            ),
            "enrollments": list(
                Enrollment.objects.filter(student=user).values(
                    "course__title", "status", "enrolled_at",
                )
            ),
            "practice_logs": list(
                PracticeLog.objects.filter(student=user).values(
                    "date", "duration_minutes", "instrument", "notes",
                )
            ),
        }
        response = JsonResponse(data, json_encoder=_DjangoJSONEncoder)
        response["Content-Disposition"] = 'attachment; filename="my_data_export.json"'
        return response


class AccountDeleteView(LoginRequiredMixin, View):
    """GDPR: Delete user account after confirmation."""

    def get(self, request):
        return render(request, "accounts/account_delete.html")

    def post(self, request):
        confirmation = request.POST.get("confirm_email", "")
        if confirmation != request.user.email:
            messages.error(request, "Email confirmation did not match. Account not deleted.")
            return redirect("account-delete")
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account has been permanently deleted.")
        return redirect("login")


class _DjangoJSONEncoder(json.JSONEncoder):
    """Handles date/datetime serialization."""

    def default(self, obj):
        from datetime import date, datetime
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)
