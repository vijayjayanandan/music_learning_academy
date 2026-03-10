import logging
import secrets

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView

from apps.accounts.models import Membership, Invitation, User
from apps.academies.models import check_seat_limit
from apps.common.audit import AuditEvent, log_audit_event
from .forms import AcademyForm, InvitationForm
from .mixins import TenantMixin
from .models import Academy, Announcement

logger = logging.getLogger(__name__)


def _send_invitation_email(invitation, request):
    """Send (or resend) an invitation email.

    Extracted from InviteMemberView and ResendInvitationView to eliminate
    duplication (DEBT-001).
    """
    accept_url = request.build_absolute_uri(
        reverse("accept-invitation", kwargs={"token": invitation.token})
    )
    try:
        html_message = render_to_string(
            "emails/invitation_email.html",
            {
                "academy": invitation.academy,
                "invited_by": request.user,
                "role": invitation.role,
                "accept_url": accept_url,
                "expires_at": invitation.expires_at,
                "user": User.objects.filter(email=invitation.email).first(),
            },
        )
        plain_message = (
            f"Hi,\n\n"
            f"{request.user.get_full_name()} has invited you to join "
            f"{invitation.academy.name} as a {invitation.role} on Music Learning Academy.\n\n"
            f"Accept the invitation here: {accept_url}\n\n"
            f"This invitation expires on {invitation.expires_at.strftime('%B %d, %Y')}."
        )
        send_mail(
            f"You've been invited to {invitation.academy.name} — Music Learning Academy",
            plain_message,
            None,  # uses DEFAULT_FROM_EMAIL
            [invitation.email],
            html_message=html_message,
        )
    except Exception:
        logger.exception("Failed to send invitation email to %s", invitation.email)


class AcademyCreateView(LoginRequiredMixin, CreateView):
    model = Academy
    form_class = AcademyForm
    template_name = "academies/create.html"

    def form_valid(self, form):
        academy = form.save(commit=False)
        academy.slug = slugify(academy.name)
        # Ensure unique slug
        base_slug = academy.slug
        counter = 1
        while Academy.objects.filter(slug=academy.slug).exists():
            academy.slug = f"{base_slug}-{counter}"
            counter += 1
        academy.save()

        # Create owner membership
        Membership.objects.create(
            user=self.request.user,
            academy=academy,
            role=Membership.Role.OWNER,
        )

        # Set as current academy
        self.request.user.current_academy = academy
        self.request.user.save(update_fields=["current_academy"])

        return redirect("academy-setup", slug=academy.slug)


class AcademyDetailView(TenantMixin, DetailView):
    model = Academy
    template_name = "academies/detail.html"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        # Security: only allow viewing academies the user is a member of
        return Academy.objects.filter(memberships__user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["members"] = Membership.objects.filter(academy=self.object).select_related(
            "user"
        )
        ctx["member_count"] = ctx["members"].count()
        return ctx


class AcademySettingsView(TenantMixin, UpdateView):
    model = Academy
    form_class = AcademyForm
    template_name = "academies/settings.html"
    slug_url_kwarg = "slug"

    def dispatch(self, request, *args, **kwargs):
        # Security: only owners can modify academy settings
        if hasattr(request, "academy") and request.academy:
            role = request.user.get_role_in(request.academy)
            if role != "owner":
                from django.http import HttpResponseForbidden

                return HttpResponseForbidden("Only academy owners can modify settings.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Security: only allow the user's own academies
        return Academy.objects.filter(memberships__user=self.request.user)

    def get_success_url(self):
        return reverse("academy-detail", kwargs={"slug": self.object.slug})


class MemberListView(TenantMixin, DetailView):
    model = Academy
    template_name = "academies/members.html"
    slug_url_kwarg = "slug"

    def dispatch(self, request, *args, **kwargs):
        # Security: only owners can manage members
        if hasattr(request, "academy") and request.academy:
            role = request.user.get_role_in(request.academy)
            if role != "owner":
                from django.http import HttpResponseForbidden

                return HttpResponseForbidden("Only academy owners can manage members.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Security: only allow the user's own academies
        return Academy.objects.filter(memberships__user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["members"] = Membership.objects.filter(academy=self.object).select_related(
            "user"
        )
        ctx["invite_form"] = InvitationForm()
        ctx["pending_invitations"] = Invitation.objects.filter(
            academy=self.object, accepted=False
        )
        ctx["academy"] = self.object
        return ctx


class InviteMemberView(TenantMixin, View):
    def post(self, request, slug):
        # Security: only owners can invite members
        academy = self.get_academy()
        role = request.user.get_role_in(academy)
        if role != "owner":
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Only academy owners can invite members.")
        # Security: ensure the slug matches the user's current academy
        if academy.slug != slug:
            from django.http import Http404

            raise Http404("Academy not found.")
        form = InvitationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            invite_role = form.cleaned_data["role"]
            # Seat limit check
            from apps.academies.models import check_seat_limit

            is_allowed, current, max_count = check_seat_limit(academy, invite_role)
            if not is_allowed:
                error_msg = f"This academy has reached its maximum of {max_count} {invite_role}s."
                if request.htmx:
                    invitations = Invitation.objects.filter(
                        academy=academy, accepted=False
                    )
                    return render(
                        request,
                        "academies/partials/_invitation_list.html",
                        {
                            "pending_invitations": invitations,
                            "academy": academy,
                            "error": error_msg,
                        },
                    )
                messages.error(request, error_msg)
                return redirect("academy-members", slug=slug)
            # Check if already a member
            if Membership.objects.filter(academy=academy, user__email=email).exists():
                if request.htmx:
                    invitations = Invitation.objects.filter(
                        academy=academy, accepted=False
                    )
                    return render(
                        request,
                        "academies/partials/_invitation_list.html",
                        {
                            "pending_invitations": invitations,
                            "academy": academy,
                            "error": "This person is already a member of this academy.",
                        },
                    )
                return redirect("academy-members", slug=slug)
            # Check for existing pending invitation
            if Invitation.objects.filter(
                academy=academy, email=email, accepted=False
            ).exists():
                if request.htmx:
                    invitations = Invitation.objects.filter(
                        academy=academy, accepted=False
                    )
                    return render(
                        request,
                        "academies/partials/_invitation_list.html",
                        {
                            "pending_invitations": invitations,
                            "academy": academy,
                            "error": "An invitation has already been sent to this email.",
                        },
                    )
                return redirect("academy-members", slug=slug)
            token = secrets.token_urlsafe(48)
            invitation = Invitation.objects.create(
                academy=academy,
                email=form.cleaned_data["email"],
                role=form.cleaned_data["role"],
                token=token,
                invited_by=request.user,
                expires_at=timezone.now() + timezone.timedelta(days=7),
            )
            # Audit log
            log_audit_event(
                action=AuditEvent.Action.MEMBER_INVITED,
                entity_type="invitation",
                entity_id=invitation.pk,
                description=f"Invited {invitation.email} as {invitation.role}",
                request=request,
            )
            # Send invitation email
            _send_invitation_email(invitation, request)
            if request.htmx:
                invitations = Invitation.objects.filter(academy=academy, accepted=False)
                return render(
                    request,
                    "academies/partials/_invitation_list.html",
                    {
                        "pending_invitations": invitations,
                        "academy": academy,
                    },
                )
        return redirect("academy-members", slug=slug)


class AcceptInvitationView(View):
    def _get_invitation(self, token):
        """Look up invitation and return (invitation, error_template) tuple."""
        # Check if already accepted
        invitation = Invitation.objects.filter(token=token).first()
        if invitation is None:
            return None, "academies/invitation_invalid.html"
        if invitation.accepted:
            return None, "academies/invitation_already_accepted.html"
        if invitation.expires_at < timezone.now():
            return None, "academies/invitation_expired.html"
        return invitation, None

    def get(self, request, token):
        invitation, error_template = self._get_invitation(token)
        if error_template:
            return render(request, error_template)
        accept_url = f"/invitation/{token}/accept/"
        return render(
            request,
            "academies/accept_invitation.html",
            {
                "invitation": invitation,
                "accept_url": accept_url,
            },
        )

    def post(self, request, token):
        invitation, error_template = self._get_invitation(token)
        if error_template:
            return render(request, error_template)

        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next=/invitation/{token}/accept/")

        # Security: only the invited email can accept
        if request.user.email.lower() != invitation.email.lower():
            return render(
                request,
                "academies/invitation_email_mismatch.html",
                {
                    "invitation": invitation,
                    "user_email": request.user.email,
                },
            )

        Membership.objects.get_or_create(
            user=request.user,
            academy=invitation.academy,
            defaults={"role": invitation.role},
        )
        invitation.accepted = True
        invitation.save()

        request.user.current_academy = invitation.academy
        request.user.save(update_fields=["current_academy"])

        messages.success(
            request,
            f"Welcome to {invitation.academy.name}! You've joined as {invitation.role}.",
        )

        # Send welcome email
        try:
            dashboard_url = request.build_absolute_uri(reverse("dashboard"))
            html_message = render_to_string(
                "emails/welcome_email.html",
                {
                    "academy": invitation.academy,
                    "user": request.user,
                    "role": invitation.role,
                    "dashboard_url": dashboard_url,
                },
            )
            plain_message = (
                f"Hi {request.user.first_name or 'there'},\n\n"
                f"Welcome to {invitation.academy.name}! "
                f"You've joined as {invitation.role}.\n\n"
                f"Go to your dashboard: {dashboard_url}"
            )
            send_mail(
                f"Welcome to {invitation.academy.name} — Music Learning Academy",
                plain_message,
                None,
                [request.user.email],
                html_message=html_message,
            )
        except Exception:
            logger.exception("Failed to send welcome email to %s", request.user.email)

        # Notify academy owners that the invitation was accepted
        from apps.notifications.models import Notification

        owner_memberships = Membership.objects.filter(
            academy=invitation.academy, role="owner"
        ).select_related("user")
        user_name = request.user.get_full_name() or request.user.email
        for m in owner_memberships:
            Notification.objects.create(
                recipient=m.user,
                academy=invitation.academy,
                notification_type="invitation",
                title="Invitation Accepted",
                message=f"{user_name} has accepted the invitation and joined as {invitation.role}.",
            )

        return redirect("dashboard")


class ResendInvitationView(TenantMixin, View):
    def post(self, request, slug, pk):
        academy = self.get_academy()
        role = request.user.get_role_in(academy)
        if role != "owner":
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Only academy owners can manage invitations.")
        invitation = get_object_or_404(
            Invitation, pk=pk, academy=academy, accepted=False
        )
        # Generate new token and extend expiry
        invitation.token = secrets.token_urlsafe(48)
        invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
        invitation.save(update_fields=["token", "expires_at"])
        # Send email
        _send_invitation_email(invitation, request)
        invitations = Invitation.objects.filter(academy=academy, accepted=False)
        return render(
            request,
            "academies/partials/_invitation_list.html",
            {
                "pending_invitations": invitations,
                "academy": academy,
                "success": f"Invitation resent to {invitation.email}.",
            },
        )


class CancelInvitationView(TenantMixin, View):
    def post(self, request, slug, pk):
        academy = self.get_academy()
        role = request.user.get_role_in(academy)
        if role != "owner":
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Only academy owners can manage invitations.")
        invitation = get_object_or_404(
            Invitation, pk=pk, academy=academy, accepted=False
        )
        invitation.delete()
        invitations = Invitation.objects.filter(academy=academy, accepted=False)
        return render(
            request,
            "academies/partials/_invitation_list.html",
            {
                "pending_invitations": invitations,
                "academy": academy,
            },
        )


class BrandedSignupView(View):
    """Public signup page for a specific academy."""

    def _get_landing_context(self, academy, form=None):
        """Build the full landing page context with courses, instructors, pricing."""
        from apps.accounts.forms import RegisterForm
        from apps.courses.models import Course
        from apps.payments.models import SubscriptionPlan, PackageDeal

        courses = Course.objects.filter(academy=academy, is_published=True)
        instructors = Membership.objects.filter(
            academy=academy, role="instructor", is_active=True
        ).select_related("user")
        plans = SubscriptionPlan.objects.filter(academy=academy, is_active=True)
        packages = PackageDeal.objects.filter(academy=academy, is_active=True)

        return {
            "academy": academy,
            "form": form or RegisterForm(),
            "courses": courses,
            "instructors": instructors,
            "plans": plans,
            "packages": packages,
        }

    def get(self, request, slug):
        academy = get_object_or_404(Academy, slug=slug)
        if request.user.is_authenticated:
            # Existing member bypass
            if Membership.objects.filter(user=request.user, academy=academy).exists():
                request.user.current_academy = academy
                request.user.save(update_fields=["current_academy"])
                return redirect("dashboard")
            # Seat limit check for new members
            is_allowed, current, max_count = check_seat_limit(academy, "student")
            if not is_allowed:
                messages.error(
                    request,
                    f"This academy has reached its maximum of {max_count} students.",
                )
                return redirect("branded-signup", slug=slug)
            # Add membership
            Membership.objects.get_or_create(
                user=request.user,
                academy=academy,
                defaults={"role": Membership.Role.STUDENT},
            )
            request.user.current_academy = academy
            request.user.save(update_fields=["current_academy"])
            return redirect("dashboard")
        context = self._get_landing_context(academy)
        return render(request, "academies/branded_signup.html", context)

    def post(self, request, slug):
        academy = get_object_or_404(Academy, slug=slug)
        from apps.accounts.forms import RegisterForm
        from apps.accounts.models import ParentalConsent
        from apps.accounts.views import _send_parental_consent_email
        from django.contrib.auth import login as auth_login
        from django.db import transaction

        form = RegisterForm(request.POST)
        if form.is_valid():
            from datetime import timedelta
            from django.utils import timezone as tz

            # Seat limit check before creating user
            is_allowed, current, max_count = check_seat_limit(academy, "student")
            if not is_allowed:
                messages.error(
                    request, f"This academy is at capacity ({max_count} students)."
                )
                return redirect("branded-signup", slug=slug)

            with transaction.atomic():
                user = form.save()

                # Save date_of_birth and terms_accepted_at (not in Meta.fields)
                update_fields = ["current_academy"]
                dob = form.cleaned_data.get("date_of_birth")
                if dob:
                    user.date_of_birth = dob
                    update_fields.append("date_of_birth")
                if form.cleaned_data.get("accept_terms"):
                    user.terms_accepted_at = tz.now()
                    update_fields.append("terms_accepted_at")

                # COPPA age-gate: under-13 users need parental consent
                if form._is_under_13():
                    parent_email = form.cleaned_data.get("parent_email", "").strip()
                    user.is_active = False
                    update_fields.append("is_active")
                    user.current_academy = academy
                    user.save(update_fields=update_fields)

                    Membership.objects.create(
                        user=user,
                        academy=academy,
                        role=Membership.Role.STUDENT,
                    )

                    consent = ParentalConsent.objects.create(
                        child=user,
                        parent_email=parent_email,
                        expires_at=tz.now() + timedelta(days=7),
                    )
                    _send_parental_consent_email(request, user, consent)

                    return render(
                        request,
                        "accounts/parental_consent_pending.html",
                        {
                            "parent_email": parent_email,
                        },
                    )

                Membership.objects.create(
                    user=user,
                    academy=academy,
                    role=Membership.Role.STUDENT,
                )
                user.current_academy = academy
                user.save(update_fields=update_fields)
                auth_login(
                    request, user, backend="django.contrib.auth.backends.ModelBackend"
                )

            # Notify academy owners about the new member
            self._notify_owners_new_member(request, user, academy)

            return redirect("dashboard")
        context = self._get_landing_context(academy, form=form)
        return render(request, "academies/branded_signup.html", context)

    def _notify_owners_new_member(self, request, user, academy):
        """Send email and in-app notification to academy owners about a new branded signup."""
        from apps.notifications.models import Notification

        user_name = user.get_full_name() or user.email
        members_url = request.build_absolute_uri(
            reverse("academy-members", kwargs={"slug": academy.slug})
        )

        owner_memberships = Membership.objects.filter(
            academy=academy, role="owner"
        ).select_related("user")

        for m in owner_memberships:
            # In-app notification
            Notification.objects.create(
                recipient=m.user,
                academy=academy,
                notification_type="enrollment",
                title="New Member Joined",
                message=f"{user_name} has joined {academy.name} as a student via branded signup.",
            )

            # Email notification
            try:
                html_message = render_to_string(
                    "emails/new_member_notification_email.html",
                    {
                        "academy": academy,
                        "owner": m.user,
                        "new_user_name": user_name,
                        "new_user_email": user.email,
                        "members_url": members_url,
                    },
                )
                plain_message = (
                    f"Hi {m.user.first_name or 'there'},\n\n"
                    f"{user_name} ({user.email}) has joined {academy.name} "
                    f"as a student via the branded signup link.\n\n"
                    f"View members: {members_url}"
                )
                send_mail(
                    f"New member joined {academy.name} — Music Learning Academy",
                    plain_message,
                    None,  # uses DEFAULT_FROM_EMAIL
                    [m.user.email],
                    html_message=html_message,
                )
            except Exception:
                logger.exception(
                    "Failed to send new member notification email to %s", m.user.email
                )


class RemoveMemberView(TenantMixin, View):
    def post(self, request, slug, pk):
        # Security: only owners can remove members
        academy = self.get_academy()
        role = request.user.get_role_in(academy)
        if role != "owner":
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Only academy owners can remove members.")
        # Security: use the current academy, not a slug-based lookup
        membership = get_object_or_404(Membership, pk=pk, academy=academy)
        if membership.role != Membership.Role.OWNER:
            before_state = {"role": membership.role, "is_active": membership.is_active}
            membership.is_active = False
            membership.membership_status = Membership.MembershipStatus.REMOVED
            membership.save(update_fields=["is_active", "membership_status"])
            log_audit_event(
                action=AuditEvent.Action.MEMBER_REMOVED,
                entity_type="membership",
                entity_id=membership.pk,
                description=f"Removed {membership.user.email} ({membership.role})",
                before_state=before_state,
                after_state={"role": membership.role, "is_active": False},
                request=request,
            )
        if request.htmx:
            members = Membership.objects.filter(academy=academy).select_related("user")
            return render(
                request,
                "academies/partials/_member_list.html",
                {
                    "members": members,
                    "academy": academy,
                },
            )
        return redirect("academy-members", slug=slug)


class AnnouncementListView(TenantMixin, View):
    def get(self, request, slug):
        # Security: use the user's current academy, not an arbitrary slug
        academy = self.get_academy()
        announcements = Announcement.objects.filter(academy=academy)
        return render(
            request,
            "academies/announcements.html",
            {
                "announcements": announcements,
                "academy": academy,
            },
        )

    def post(self, request, slug):
        # Security: only owners and instructors can create announcements
        academy = self.get_academy()
        role = request.user.get_role_in(academy)
        if role not in ("owner", "instructor"):
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden(
                "Only owners and instructors can create announcements."
            )
        Announcement.objects.create(
            academy=academy,
            author=request.user,
            title=request.POST.get("title", ""),
            body=request.POST.get("body", ""),
            is_pinned="is_pinned" in request.POST,
        )
        return redirect("academy-announcements", slug=academy.slug)


class SetupWizardView(LoginRequiredMixin, DetailView):
    model = Academy
    template_name = "academies/setup_wizard.html"

    def dispatch(self, request, *args, **kwargs):
        academy = self.get_object()
        role = request.user.get_role_in(academy)
        if role != "owner":
            return HttpResponseForbidden("Owner access required")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        academy = self.get_object()
        # Determine current step from setup_status
        status_to_step = {
            "new": "basics",
            "basics_done": "branding",
            "branding_done": "team",
            "team_invited": "course",
            "catalog_ready": "launch",
            "live": "launch",
        }
        ctx["current_step"] = status_to_step.get(academy.setup_status, "basics")
        ctx["step"] = ctx["current_step"]
        ctx["setup_progress"] = academy.setup_progress
        ctx["academy"] = academy
        ctx["steps"] = ["basics", "branding", "team", "course", "launch"]
        ctx["completed_steps"] = []
        step_order = ["basics", "branding", "team", "course", "launch"]
        current_idx = (
            step_order.index(ctx["current_step"])
            if ctx["current_step"] in step_order
            else 0
        )
        ctx["completed_steps"] = step_order[:current_idx]
        # Provide form for basics step
        if ctx["current_step"] == "basics":
            from apps.academies.forms import AcademyBasicsForm

            ctx["form"] = AcademyBasicsForm(instance=academy)
        elif ctx["current_step"] == "branding":
            from apps.academies.forms import AcademyBrandingForm

            ctx["form"] = AcademyBrandingForm(instance=academy)
        return ctx


class SetupWizardStepView(LoginRequiredMixin, DetailView):
    model = Academy
    template_name = "academies/setup_wizard.html"

    def dispatch(self, request, *args, **kwargs):
        academy = self.get_object()
        role = request.user.get_role_in(academy)
        if role != "owner":
            return HttpResponseForbidden("Owner access required")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        academy = self.get_object()
        step = self.kwargs.get("step", "basics")
        ctx["current_step"] = step
        ctx["step"] = step
        ctx["setup_progress"] = academy.setup_progress
        ctx["academy"] = academy
        ctx["steps"] = ["basics", "branding", "team", "course", "launch"]
        step_order = ["basics", "branding", "team", "course", "launch"]
        current_idx = step_order.index(step) if step in step_order else 0
        ctx["completed_steps"] = step_order[:current_idx]
        # Progress for launch step
        completed, total, pct = academy.setup_progress
        ctx["progress_pct"] = pct
        ctx["completed"] = completed
        ctx["total"] = total
        # Signup URL and QR URL for launch step
        ctx["signup_url"] = self.request.build_absolute_uri(f"/join/{academy.slug}/")
        ctx["qr_url"] = reverse("academy-qr-code", args=[academy.slug])
        # Forms
        if step == "basics":
            from apps.academies.forms import AcademyBasicsForm

            ctx["form"] = AcademyBasicsForm(instance=academy)
        elif step == "branding":
            from apps.academies.forms import AcademyBrandingForm

            ctx["form"] = AcademyBrandingForm(instance=academy)
        elif step == "team":
            from apps.academies.forms import InvitationForm

            ctx["invite_form"] = InvitationForm()
            ctx["members"] = Membership.objects.filter(academy=academy).select_related(
                "user"
            )
        elif step == "course":
            from apps.courses.models import Course

            ctx["courses"] = Course.objects.filter(academy=academy)
        return ctx

    def post(self, request, *args, **kwargs):
        academy = self.get_object()
        step = self.kwargs.get("step", "basics")

        step_advancement = {
            "basics": ("basics_done", "branding"),
            "branding": ("branding_done", "team"),
            "team": ("team_invited", "course"),
            "course": ("catalog_ready", "launch"),
            "launch": ("live", None),
        }

        if step == "basics":
            from apps.academies.forms import AcademyBasicsForm

            form = AcademyBasicsForm(request.POST, instance=academy)
            if form.is_valid():
                form.save()
        elif step == "branding":
            from apps.academies.forms import AcademyBrandingForm

            form = AcademyBrandingForm(request.POST, instance=academy)
            if form.is_valid():
                form.save()

        new_status, next_step = step_advancement.get(step, ("new", "basics"))
        academy.setup_status = new_status
        academy.save(update_fields=["setup_status"])

        if next_step:
            return redirect(
                reverse("academy-setup-step", args=[academy.slug, next_step])
            )
        return redirect("dashboard")


class ShareLinkView(LoginRequiredMixin, DetailView):
    model = Academy
    template_name = "academies/share_link.html"

    def dispatch(self, request, *args, **kwargs):
        academy = self.get_object()
        role = request.user.get_role_in(academy)
        if role != "owner":
            return HttpResponseForbidden("Owner access required")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        academy = self.get_object()
        ctx["signup_url"] = self.request.build_absolute_uri(f"/join/{academy.slug}/")
        ctx["qr_url"] = reverse("academy-qr-code", args=[academy.slug])
        return ctx


class QRCodeView(LoginRequiredMixin, DetailView):
    model = Academy

    def dispatch(self, request, *args, **kwargs):
        academy = self.get_object()
        role = request.user.get_role_in(academy)
        if role != "owner":
            return HttpResponseForbidden("Owner access required")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        import io

        try:
            import qrcode

            academy = self.get_object()
            signup_url = request.build_absolute_uri(f"/join/{academy.slug}/")
            img = qrcode.make(signup_url)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return HttpResponse(buf.getvalue(), content_type="image/png")
        except ImportError:
            # qrcode not installed -- return a minimal 1x1 PNG
            import struct
            import zlib

            def minimal_png():
                sig = b"\x89PNG\r\n\x1a\n"
                ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
                ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
                ihdr = (
                    struct.pack(">I", 13)
                    + b"IHDR"
                    + ihdr_data
                    + struct.pack(">I", ihdr_crc)
                )
                raw = b"\x00\x00\x00\x00"
                idat_data = zlib.compress(raw)
                idat_crc = zlib.crc32(b"IDAT" + idat_data) & 0xFFFFFFFF
                idat = (
                    struct.pack(">I", len(idat_data))
                    + b"IDAT"
                    + idat_data
                    + struct.pack(">I", idat_crc)
                )
                iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
                iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)
                return sig + ihdr + idat + iend

            return HttpResponse(minimal_png(), content_type="image/png")
