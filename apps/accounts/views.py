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

    def get_success_url(self):
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url:
            return next_url
        return str(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["next"] = self.request.GET.get("next", "")
        return ctx

    def form_valid(self, form):
        from django.utils import timezone as tz

        response = super().form_valid(form)
        user = self.object

        # Save date_of_birth and terms_accepted_at (not in Meta.fields)
        update_fields = []
        dob = form.cleaned_data.get("date_of_birth")
        if dob:
            user.date_of_birth = dob
            update_fields.append("date_of_birth")
        if form.cleaned_data.get("accept_terms"):
            user.terms_accepted_at = tz.now()
            update_fields.append("terms_accepted_at")
        if update_fields:
            user.save(update_fields=update_fields)

        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        _send_verification_email(self.request, user)
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
        # Add current membership for Learning Preferences section (students only)
        academy = getattr(self.request, "academy", None)
        if academy:
            ctx["membership"] = self.request.user.memberships.filter(academy=academy).first()
        return ctx


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("profile")

    # Default instruments when academy doesn't specify any
    DEFAULT_INSTRUMENTS = ["Piano", "Guitar", "Violin", "Voice", "Drums", "Bass", "Cello", "Flute", "Saxophone", "Other"]

    def get_object(self):
        return self.request.user

    def _get_membership(self):
        """Return the current user's membership in the active academy, or None."""
        academy = getattr(self.request, "academy", None)
        if academy:
            return self.request.user.memberships.filter(academy=academy).first()
        return None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        membership = self._get_membership()
        ctx["membership"] = membership
        # Provide the list of instruments for checkbox selection
        academy = getattr(self.request, "academy", None)
        if academy and academy.primary_instruments:
            ctx["available_instruments"] = academy.primary_instruments
        else:
            ctx["available_instruments"] = self.DEFAULT_INSTRUMENTS
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        # Save learning preferences for student memberships
        membership = self._get_membership()
        if membership and membership.role == "student":
            membership.skill_level = self.request.POST.get("skill_level", membership.skill_level)
            membership.learning_goal = self.request.POST.get("learning_goal", membership.learning_goal)
            instruments = self.request.POST.getlist("instruments")
            if instruments:
                membership.instruments = instruments
            else:
                membership.instruments = []
            membership.save(update_fields=["skill_level", "learning_goal", "instruments"])
        return response


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
    """GDPR: Export all user data as JSON, including file URLs."""

    def _file_url(self, file_field):
        """Generate a URL for a file field (signed if R2, local otherwise)."""
        if file_field and file_field.name:
            try:
                return file_field.url
            except Exception:
                return None
        return None

    def get(self, request):
        user = request.user
        from apps.enrollments.models import AssignmentSubmission
        from apps.enrollments.models import Enrollment
        from apps.music_tools.models import PracticeAnalysis, RecordingArchive
        from apps.practice.models import PracticeLog

        # Collect file URLs for user's uploads
        submissions = AssignmentSubmission.objects.filter(student=user)
        submission_files = []
        for sub in submissions:
            entry = {"assignment": str(sub.assignment), "status": sub.status}
            if sub.recording and sub.recording.name:
                entry["recording_url"] = self._file_url(sub.recording)
            if sub.file_upload and sub.file_upload.name:
                entry["file_url"] = self._file_url(sub.file_upload)
            submission_files.append(entry)

        recordings = RecordingArchive.objects.filter(student=user)
        recording_files = [
            {
                "title": r.title,
                "instrument": r.instrument,
                "url": self._file_url(r.recording),
                "created_at": r.created_at.isoformat(),
            }
            for r in recordings
        ]

        analyses = PracticeAnalysis.objects.filter(student=user)
        analysis_files = [
            {
                "feedback": a.feedback,
                "recording_url": self._file_url(a.recording),
                "created_at": a.created_at.isoformat(),
            }
            for a in analyses
        ]

        data = {
            "account": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "date_joined": user.date_joined.isoformat(),
                "timezone": str(getattr(user, "timezone", "")),
                "avatar_url": self._file_url(user.avatar),
            },
            "memberships": list(
                user.memberships.select_related("academy").values(
                    "academy__name", "role", "joined_at",
                )
            ),
            "enrollments": list(
                Enrollment.objects.filter(student=user).values(
                    "course__title", "status", "enrolled_at",
                )
            ),
            "assignment_submissions": submission_files,
            "recordings": recording_files,
            "practice_analyses": analysis_files,
            "practice_logs": list(
                PracticeLog.objects.filter(student=user).values(
                    "date", "duration_minutes", "instrument", "notes",
                )
            ),
        }
        response = JsonResponse(data, encoder=_DjangoJSONEncoder)
        response["Content-Disposition"] = 'attachment; filename="my_data_export.json"'
        return response


class AccountDeleteView(LoginRequiredMixin, View):
    """GDPR: Delete user account after confirmation.

    File cleanup is handled by post_delete signals in apps/common/signals.py,
    which automatically delete R2/storage files when models are cascade-deleted.
    """

    def get(self, request):
        return render(request, "accounts/account_delete.html")

    def post(self, request):
        confirmation = request.POST.get("confirm_email", "")
        if confirmation != request.user.email:
            messages.error(request, "Email confirmation did not match. Account not deleted.")
            return redirect("account-delete")
        user = request.user
        logout(request)
        # post_delete signals handle R2 file cleanup for user avatar
        # and all related models (submissions, recordings, etc.) via CASCADE
        user.delete()
        messages.success(request, "Your account has been permanently deleted.")
        return redirect("login")


class ApproveParentalConsentView(TemplateView):
    template_name = "accounts/parental_consent_result.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        token = self.kwargs.get("token")

        try:
            from apps.accounts.models import ParentalConsent
            consent = ParentalConsent.objects.get(token=token)
        except ParentalConsent.DoesNotExist:
            ctx["success"] = False
            ctx["reason"] = "invalid"
            return ctx

        from django.utils import timezone as tz
        now = tz.now()

        if consent.expires_at < now:
            ctx["success"] = False
            ctx["reason"] = "expired"
            return ctx

        if consent.approved_at is not None:
            ctx["success"] = True
            ctx["reason"] = "already_approved"
            ctx["child"] = consent.child
            return ctx

        # Approve
        child = consent.child
        child.is_active = True
        child.parental_consent_given = True
        child.save(update_fields=["is_active", "parental_consent_given"])

        consent.approved_at = now
        consent.save(update_fields=["approved_at"])

        ctx["success"] = True
        ctx["reason"] = "approved"
        ctx["child"] = child
        return ctx


class _DjangoJSONEncoder(json.JSONEncoder):
    """Handles date/datetime serialization."""

    def default(self, obj):
        from datetime import date, datetime
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)
