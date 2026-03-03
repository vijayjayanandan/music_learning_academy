from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.shortcuts import redirect, get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView

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
    message = render_to_string("accounts/email_verification_email.html", {
        "user": user,
        "verify_url": verify_url,
    })
    send_mail(
        "Verify your email - Music Learning Academy",
        message,
        None,  # uses DEFAULT_FROM_EMAIL
        [user.email],
    )


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("login")


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
    """Link a child account to parent."""

    def post(self, request):
        child_email = request.POST.get("child_email", "")
        try:
            child = User.objects.get(email=child_email)
            child.parent = request.user
            child.save(update_fields=["parent"])
            request.user.is_parent = True
            request.user.save(update_fields=["is_parent"])
        except User.DoesNotExist:
            pass
        return redirect("parent-dashboard")
