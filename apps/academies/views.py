import secrets
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView

from apps.accounts.models import Membership, Invitation, User
from .forms import AcademyForm, InvitationForm
from .mixins import TenantMixin
from .models import Academy


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

        return redirect("academy-detail", slug=academy.slug)


class AcademyDetailView(TenantMixin, DetailView):
    model = Academy
    template_name = "academies/detail.html"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Academy.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["members"] = Membership.objects.filter(
            academy=self.object
        ).select_related("user")
        ctx["member_count"] = ctx["members"].count()
        return ctx


class AcademySettingsView(TenantMixin, UpdateView):
    model = Academy
    form_class = AcademyForm
    template_name = "academies/settings.html"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Academy.objects.all()

    def get_success_url(self):
        return reverse("academy-detail", kwargs={"slug": self.object.slug})


class MemberListView(TenantMixin, DetailView):
    model = Academy
    template_name = "academies/members.html"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Academy.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["members"] = Membership.objects.filter(
            academy=self.object
        ).select_related("user")
        ctx["invite_form"] = InvitationForm()
        ctx["pending_invitations"] = Invitation.objects.filter(
            academy=self.object, accepted=False
        )
        return ctx


class InviteMemberView(TenantMixin, View):
    def post(self, request, slug):
        academy = get_object_or_404(Academy, slug=slug)
        form = InvitationForm(request.POST)
        if form.is_valid():
            token = secrets.token_urlsafe(48)
            Invitation.objects.create(
                academy=academy,
                email=form.cleaned_data["email"],
                role=form.cleaned_data["role"],
                token=token,
                invited_by=request.user,
                expires_at=timezone.now() + timezone.timedelta(days=7),
            )
            if request.htmx:
                invitations = Invitation.objects.filter(academy=academy, accepted=False)
                return render(request, "academies/partials/_invitation_list.html", {
                    "pending_invitations": invitations,
                    "academy": academy,
                })
        return redirect("academy-members", slug=slug)


class AcceptInvitationView(View):
    def get(self, request, token):
        invitation = get_object_or_404(Invitation, token=token, accepted=False)
        if invitation.expires_at < timezone.now():
            return render(request, "academies/invitation_expired.html")
        return render(request, "academies/accept_invitation.html", {
            "invitation": invitation,
        })

    def post(self, request, token):
        invitation = get_object_or_404(Invitation, token=token, accepted=False)
        if invitation.expires_at < timezone.now():
            return render(request, "academies/invitation_expired.html")

        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next=/invitation/{token}/accept/")

        Membership.objects.get_or_create(
            user=request.user,
            academy=invitation.academy,
            defaults={"role": invitation.role},
        )
        invitation.accepted = True
        invitation.save()

        request.user.current_academy = invitation.academy
        request.user.save(update_fields=["current_academy"])

        return redirect("dashboard")


class RemoveMemberView(TenantMixin, View):
    def post(self, request, slug, pk):
        academy = get_object_or_404(Academy, slug=slug)
        membership = get_object_or_404(Membership, pk=pk, academy=academy)
        if membership.role != Membership.Role.OWNER:
            membership.delete()
        if request.htmx:
            members = Membership.objects.filter(academy=academy).select_related("user")
            return render(request, "academies/partials/_member_list.html", {
                "members": members, "academy": academy,
            })
        return redirect("academy-members", slug=slug)
