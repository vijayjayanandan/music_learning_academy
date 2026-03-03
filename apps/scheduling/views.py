import json
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from apps.academies.mixins import TenantMixin
from .forms import LiveSessionForm
from .jitsi import generate_jitsi_room_name, get_jitsi_config
from .models import LiveSession, SessionAttendance


class ScheduleListView(TenantMixin, ListView):
    model = LiveSession
    template_name = "scheduling/calendar.html"
    context_object_name = "sessions"

    def get_queryset(self):
        return super().get_queryset().filter(
            scheduled_start__gte=timezone.now(),
            status="scheduled",
        ).select_related("instructor", "course").order_by("scheduled_start")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["past_sessions"] = LiveSession.objects.filter(
            academy=self.get_academy(),
            scheduled_start__lt=timezone.now(),
        ).select_related("instructor", "course").order_by("-scheduled_start")[:10]
        return ctx


class SessionCreateView(TenantMixin, CreateView):
    model = LiveSession
    form_class = LiveSessionForm
    template_name = "scheduling/session_create.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["academy"] = self.get_academy()
        return kwargs

    def form_valid(self, form):
        session = form.save(commit=False)
        session.academy = self.get_academy()
        session.instructor = self.request.user
        session.jitsi_room_name = generate_jitsi_room_name(
            self.get_academy().slug, id(session)
        )
        session.save()
        return redirect("session-detail", pk=session.pk)


class SessionDetailView(TenantMixin, DetailView):
    model = LiveSession
    template_name = "scheduling/session_detail.html"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["session"] = self.object
        ctx["attendances"] = self.object.attendances.select_related("student").all()
        ctx["is_instructor"] = self.object.instructor == self.request.user
        ctx["is_registered"] = self.object.attendances.filter(
            student=self.request.user
        ).exists()
        ctx["can_join"] = (
            ctx["is_instructor"]
            or ctx["is_registered"]
        )
        return ctx


class SessionEditView(TenantMixin, UpdateView):
    model = LiveSession
    form_class = LiveSessionForm
    template_name = "scheduling/session_edit.html"
    pk_url_kwarg = "pk"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["academy"] = self.get_academy()
        return kwargs

    def get_success_url(self):
        return self.object.get_absolute_url() if hasattr(self.object, 'get_absolute_url') else f"/schedule/session/{self.object.pk}/"


class CancelSessionView(TenantMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(
            LiveSession, pk=pk, academy=self.get_academy()
        )
        session.status = LiveSession.SessionStatus.CANCELLED
        session.save()
        if request.htmx:
            return render(request, "scheduling/partials/_session_card.html", {
                "session": session,
            })
        return redirect("schedule-list")


class RegisterForSessionView(TenantMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(
            LiveSession, pk=pk, academy=self.get_academy()
        )
        attendance, created = SessionAttendance.objects.get_or_create(
            session=session,
            student=request.user,
            academy=self.get_academy(),
        )
        if request.htmx:
            return render(request, "scheduling/partials/_register_button.html", {
                "session": session, "is_registered": True,
            })
        return redirect("session-detail", pk=pk)


class JoinSessionView(TenantMixin, DetailView):
    model = LiveSession
    template_name = "scheduling/video_room.html"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        session = self.object
        user = self.request.user

        is_instructor = session.instructor == user
        is_registered = session.attendances.filter(student=user).exists()

        if not is_instructor and not is_registered:
            raise PermissionDenied("You are not registered for this session.")

        ctx["jitsi_config"] = json.dumps(get_jitsi_config(session, user))
        ctx["jitsi_domain"] = settings.JITSI_DOMAIN
        ctx["session"] = session
        return ctx


class MarkJoinedView(TenantMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(LiveSession, pk=pk)
        SessionAttendance.objects.filter(
            session=session, student=request.user
        ).update(
            status=SessionAttendance.AttendanceStatus.ATTENDED,
            joined_at=timezone.now(),
        )
        return render(request, "scheduling/partials/_attendance_status.html", {
            "status": "joined",
        })


class MarkLeftView(TenantMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(LiveSession, pk=pk)
        SessionAttendance.objects.filter(
            session=session, student=request.user
        ).update(left_at=timezone.now())
        return render(request, "scheduling/partials/_attendance_status.html", {
            "status": "left",
        })


class UpcomingSessionsPartialView(TenantMixin, ListView):
    model = LiveSession
    template_name = "scheduling/partials/_upcoming_sessions.html"
    context_object_name = "sessions"

    def get_queryset(self):
        return super().get_queryset().filter(
            scheduled_start__gte=timezone.now(),
            status="scheduled",
        ).select_related("instructor", "course")[:5]
