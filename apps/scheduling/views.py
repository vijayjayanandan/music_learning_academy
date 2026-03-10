import json
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from apps.academies.mixins import TenantMixin
from apps.notifications.models import Notification
from .forms import LiveSessionForm
from .jitsi import generate_room_name, get_jitsi_config
from .models import LiveSession, SessionAttendance, InstructorAvailability


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

    def dispatch(self, request, *args, **kwargs):
        # Security: only instructors and owners can create sessions
        if hasattr(request, 'academy') and request.academy:
            role = request.user.get_role_in(request.academy)
            if role not in ("owner", "instructor"):
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Only instructors and owners can create sessions.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["academy"] = self.get_academy()
        return kwargs

    def form_valid(self, form):
        session = form.save(commit=False)
        session.academy = self.get_academy()
        session.instructor = self.request.user

        # Check for double-booking overlap
        overlap = LiveSession.objects.filter(
            instructor=session.instructor,
            academy=session.academy,
            status=LiveSession.SessionStatus.SCHEDULED,
            scheduled_start__lt=session.scheduled_end,
            scheduled_end__gt=session.scheduled_start,
        ).exists()
        if overlap:
            form.add_error(None, "This session overlaps with an existing scheduled session.")
            return self.form_invalid(form)

        session.room_name = generate_room_name(
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
        ctx["user_role"] = self.request.user.get_role_in(self.get_academy())
        return ctx


class SessionEditView(TenantMixin, UpdateView):
    model = LiveSession
    form_class = LiveSessionForm
    template_name = "scheduling/session_edit.html"
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        # Security: only instructors and owners can edit sessions
        if hasattr(request, 'academy') and request.academy:
            role = request.user.get_role_in(request.academy)
            if role not in ("owner", "instructor"):
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Only instructors and owners can edit sessions.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["academy"] = self.get_academy()
        return kwargs

    def get_success_url(self):
        return self.object.get_absolute_url() if hasattr(self.object, 'get_absolute_url') else f"/schedule/session/{self.object.pk}/"


class CancelSessionView(TenantMixin, View):
    def post(self, request, pk):
        # Security: only the session instructor or academy owner can cancel
        role = request.user.get_role_in(self.get_academy())
        if role not in ("owner", "instructor"):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Only instructors and owners can cancel sessions.")
        session = get_object_or_404(
            LiveSession, pk=pk, academy=self.get_academy()
        )
        # Additional check: instructors can only cancel their own sessions
        if role == "instructor" and session.instructor != request.user:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You can only cancel your own sessions.")
        before_status = session.status
        session.status = LiveSession.SessionStatus.CANCELLED
        session.save()
        from apps.common.audit import AuditEvent, log_audit_event
        log_audit_event(
            action=AuditEvent.Action.SESSION_CANCELLED,
            entity_type="session",
            entity_id=session.pk,
            description=f"Cancelled session: {session.title}",
            before_state={"status": before_status},
            after_state={"status": "cancelled"},
            request=request,
        )
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

        # Capacity check: 0 means unlimited
        if session.max_participants > 0:
            current_count = session.attendances.count()
            if current_count >= session.max_participants:
                from django.contrib import messages as django_messages
                django_messages.error(request, "This session is full.")
                return redirect("session-detail", pk=pk)

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

        # Check if LiveKit is configured
        livekit_url = getattr(settings, "LIVEKIT_URL", "")
        livekit_key = getattr(settings, "LIVEKIT_API_KEY", "")
        livekit_secret = getattr(settings, "LIVEKIT_API_SECRET", "")

        if livekit_url and livekit_key and livekit_secret:
            from apps.scheduling.livekit_service import get_livekit_config
            ctx["use_livekit"] = True
            ctx["livekit_config"] = json.dumps(get_livekit_config(session, user))
        else:
            ctx["use_livekit"] = False
            ctx["jitsi_config"] = json.dumps(get_jitsi_config(session, user))
            ctx["jitsi_domain"] = settings.JITSI_DOMAIN

        ctx["session"] = session
        return ctx


class MarkJoinedView(TenantMixin, View):
    def post(self, request, pk):
        # Security: filter by academy (tenant isolation)
        session = get_object_or_404(LiveSession, pk=pk, academy=self.get_academy())
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
        # Security: filter by academy (tenant isolation)
        session = get_object_or_404(LiveSession, pk=pk, academy=self.get_academy())
        SessionAttendance.objects.filter(
            session=session, student=request.user
        ).update(left_at=timezone.now())
        return render(request, "scheduling/partials/_attendance_status.html", {
            "status": "left",
        })


class SessionEventsAPIView(TenantMixin, View):
    """JSON API for FullCalendar events."""

    def get(self, request):
        from django.http import JsonResponse

        start = request.GET.get("start")
        end = request.GET.get("end")
        qs = LiveSession.objects.filter(academy=self.get_academy())
        if start:
            qs = qs.filter(scheduled_end__gte=start)
        if end:
            qs = qs.filter(scheduled_start__lte=end)
        qs = qs.select_related("instructor", "course")

        color_map = {
            "one_on_one": "#3B82F6",
            "group": "#10B981",
            "masterclass": "#8B5CF6",
            "recital": "#F59E0B",
        }
        events = []
        for s in qs:
            events.append({
                "id": s.pk,
                "title": s.title,
                "start": s.scheduled_start.isoformat(),
                "end": s.scheduled_end.isoformat(),
                "url": f"/schedule/session/{s.pk}/",
                "color": color_map.get(s.session_type, "#6B7280"),
                "classNames": ["opacity-50"] if s.status == "cancelled" else [],
                "extendedProps": {
                    "type": s.get_session_type_display(),
                    "instructor": s.instructor.get_full_name() or s.instructor.email,
                    "status": s.status,
                },
            })
        return JsonResponse(events, safe=False)


class AvailabilityManageView(TenantMixin, View):
    """FEAT-030: Instructor manages availability slots."""

    def dispatch(self, request, *args, **kwargs):
        # Security: only instructors (and owners) can manage availability
        if hasattr(request, 'academy') and request.academy:
            role = request.user.get_role_in(request.academy)
            if role not in ("owner", "instructor"):
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Only instructors can manage availability.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        slots = InstructorAvailability.objects.filter(
            instructor=request.user, academy=self.get_academy(),
        )
        return render(request, "scheduling/availability.html", {"slots": slots})

    def post(self, request):
        # Security: validate day_of_week is in range 0-6
        try:
            day = int(request.POST.get("day_of_week", 0))
            day = max(0, min(day, 6))
        except (ValueError, TypeError):
            day = 0
        InstructorAvailability.objects.create(
            instructor=request.user,
            academy=self.get_academy(),
            day_of_week=day,
            start_time=request.POST.get("start_time"),
            end_time=request.POST.get("end_time"),
        )
        return redirect("availability-manage")


class DeleteAvailabilityView(TenantMixin, View):
    def dispatch(self, request, *args, **kwargs):
        # Security: only instructors can manage availability
        if hasattr(request, 'academy') and request.academy:
            role = request.user.get_role_in(request.academy)
            if role not in ("owner", "instructor"):
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Only instructors can manage availability.")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        # Security: filter by academy too (tenant isolation)
        slot = get_object_or_404(
            InstructorAvailability, pk=pk, instructor=request.user,
            academy=self.get_academy(),
        )
        slot.delete()
        return redirect("availability-manage")


class BookSessionView(TenantMixin, View):
    """FEAT-030: Student self-booking from instructor availability (3-step wizard)."""

    def get(self, request):
        from apps.accounts.models import Membership
        instructors = Membership.objects.filter(
            academy=self.get_academy(), role="instructor",
        ).select_related("user")
        return render(request, "scheduling/book_session.html", {
            "instructors": instructors,
        })

    def post(self, request):
        from apps.accounts.models import User, Membership
        from datetime import datetime, date
        from django.contrib import messages as django_messages

        instructor = get_object_or_404(User, pk=request.POST.get("instructor"))
        # Security: verify instructor is actually an instructor in this academy
        if not Membership.objects.filter(
            user=instructor, academy=self.get_academy(), role="instructor"
        ).exists():
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Invalid instructor for this academy.")
        # Security: filter slot by academy (tenant isolation)
        slot = get_object_or_404(
            InstructorAvailability, pk=request.POST.get("slot"),
            academy=self.get_academy(),
        )
        session_date_str = request.POST.get("session_date")

        try:
            session_date = datetime.strptime(session_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return self._error_response(request, "Invalid date format.")

        # Validate: not in the past
        if session_date < date.today():
            return self._error_response(request, "Cannot book a session in the past.")

        # Validate: day-of-week matches the slot
        if session_date.weekday() != slot.day_of_week:
            return self._error_response(
                request,
                f"The selected date ({session_date.strftime('%A')}) does not match "
                f"the slot day ({slot.get_day_of_week_display()})."
            )

        start_dt = datetime.combine(session_date, slot.start_time)
        end_dt = datetime.combine(session_date, slot.end_time)
        from django.utils import timezone as tz
        start_dt = tz.make_aware(start_dt)
        end_dt = tz.make_aware(end_dt)

        # Check for double-booking
        existing = LiveSession.objects.filter(
            instructor=instructor,
            academy=self.get_academy(),
            scheduled_start=start_dt,
            status="scheduled",
        ).exists()
        if existing:
            return self._error_response(request, "This slot is already booked for the selected date.")

        # Custom title or default
        custom_title = request.POST.get("session_title", "").strip()
        default_title = f"Lesson with {instructor.get_full_name() or instructor.email}"
        title = custom_title or default_title

        session = LiveSession.objects.create(
            title=title,
            instructor=instructor,
            academy=self.get_academy(),
            scheduled_start=start_dt,
            scheduled_end=end_dt,
            session_type="one_on_one",
            room_name=generate_room_name(self.get_academy().slug, id(start_dt)),
        )
        SessionAttendance.objects.create(
            session=session, student=request.user, academy=self.get_academy(),
        )

        # Booking notifications
        session_link = reverse("session-detail", args=[session.pk])
        date_str = session_date.strftime('%b %d, %Y')
        time_str = slot.start_time.strftime('%H:%M')
        student_name = request.user.get_full_name() or request.user.email
        instructor_name = instructor.get_full_name() or instructor.email

        # Notify instructor
        Notification.objects.create(
            recipient=instructor,
            academy=self.get_academy(),
            notification_type=Notification.NotificationType.SESSION_BOOKED,
            title="New Session Booked",
            message=f"{student_name} booked a lesson on {date_str} at {time_str}",
            link=session_link,
        )
        # Confirm to student
        Notification.objects.create(
            recipient=request.user,
            academy=self.get_academy(),
            notification_type=Notification.NotificationType.SESSION_BOOKED,
            title="Booking Confirmed",
            message=f"Your lesson with {instructor_name} is confirmed for {date_str} at {time_str}",
            link=session_link,
        )

        django_messages.success(
            request,
            f"Session booked! {title} on {session_date.strftime('%b %d, %Y')} "
            f"at {slot.start_time.strftime('%H:%M')}."
        )
        return redirect("session-detail", pk=session.pk)

    def _error_response(self, request, error_msg):
        from apps.accounts.models import Membership
        instructors = Membership.objects.filter(
            academy=self.get_academy(), role="instructor",
        ).select_related("user")
        return render(request, "scheduling/book_session.html", {
            "instructors": instructors,
            "error": error_msg,
        })


class BookSessionSlotsView(TenantMixin, View):
    """HTMX partial: loads available slots for a selected instructor."""

    def get(self, request):
        instructor_id = request.GET.get("instructor")
        if not instructor_id:
            return render(request, "scheduling/partials/_booking_slots.html", {
                "slots": [],
            })
        slots = InstructorAvailability.objects.filter(
            instructor_id=instructor_id,
            academy=self.get_academy(),
            is_active=True,
        )
        return render(request, "scheduling/partials/_booking_slots.html", {
            "slots": slots,
            "instructor_id": instructor_id,
        })


class BookSessionConfirmView(TenantMixin, View):
    """HTMX partial: shows booking confirmation summary."""

    def post(self, request):
        from apps.accounts.models import User, Membership
        from datetime import datetime

        instructor_id = request.POST.get("instructor")
        slot_id = request.POST.get("slot")
        session_date_str = request.POST.get("session_date")

        try:
            instructor = User.objects.get(pk=instructor_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return render(request, "scheduling/partials/_booking_error.html", {
                "error": "Invalid instructor selected.",
            })

        # Security: verify instructor belongs to this academy
        if not Membership.objects.filter(
            user=instructor, academy=self.get_academy(), role="instructor"
        ).exists():
            return render(request, "scheduling/partials/_booking_error.html", {
                "error": "Instructor not found in this academy.",
            })

        try:
            slot = InstructorAvailability.objects.get(
                pk=slot_id, academy=self.get_academy()
            )
        except (InstructorAvailability.DoesNotExist, ValueError, TypeError):
            return render(request, "scheduling/partials/_booking_error.html", {
                "error": "Invalid time slot selected.",
            })

        try:
            session_date = datetime.strptime(session_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return render(request, "scheduling/partials/_booking_error.html", {
                "error": "Invalid date format.",
            })

        # Validate day-of-week match
        if session_date.weekday() != slot.day_of_week:
            return render(request, "scheduling/partials/_booking_error.html", {
                "error": f"The selected date ({session_date.strftime('%A')}) does not match "
                         f"the slot day ({slot.get_day_of_week_display()}).",
            })

        default_title = f"Lesson with {instructor.get_full_name() or instructor.email}"

        return render(request, "scheduling/partials/_booking_confirm.html", {
            "instructor": instructor,
            "slot": slot,
            "session_date": session_date,
            "default_title": default_title,
        })


class RescheduleSessionView(TenantMixin, View):
    """Reschedule a session: creates a new session and marks old as rescheduled.

    Permissions:
    - Instructor: can reschedule their own sessions (any type)
    - Owner: can reschedule any session
    - Student: can reschedule one_on_one sessions they're registered for (24h notice)
    """

    MIN_NOTICE_HOURS = 24  # Students must reschedule at least 24h before session

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            LiveSession, pk=kwargs["pk"], academy=self.get_academy()
        )
        role = request.user.get_role_in(self.get_academy())
        is_own_instructor = (
            role == "instructor" and self.session.instructor == request.user
        )
        is_owner = role == "owner"
        # Student: only one_on_one sessions they're registered for
        is_student_own = (
            role == "student"
            and self.session.session_type == "one_on_one"
            and SessionAttendance.objects.filter(
                session=self.session, student=request.user
            ).exists()
        )
        if not (is_own_instructor or is_owner or is_student_own):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You do not have permission to reschedule this session.")

        # Students must give 24h notice
        if is_student_own:
            hours_until = (self.session.scheduled_start - timezone.now()).total_seconds() / 3600
            if hours_until < self.MIN_NOTICE_HOURS:
                from django.contrib import messages as django_messages
                django_messages.error(
                    request,
                    f"Rescheduling requires at least {self.MIN_NOTICE_HOURS} hours notice."
                )
                return redirect("session-detail", pk=self.session.pk)

            # Reschedule limit enforcement for students
            limit = self.get_academy().reschedule_limit
            if limit > 0:
                month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                reschedule_count = LiveSession.objects.filter(
                    academy=self.get_academy(),
                    rescheduled_from__isnull=False,
                    attendances__student=request.user,
                    created_at__gte=month_start,
                ).count()
                if reschedule_count >= limit:
                    from django.contrib import messages as django_messages
                    django_messages.error(
                        request,
                        f"You have reached your reschedule limit of {limit} per month."
                    )
                    return redirect("session-detail", pk=self.session.pk)

        self.user_role = role
        # Can only reschedule scheduled sessions
        if self.session.status != LiveSession.SessionStatus.SCHEDULED:
            return redirect("session-detail", pk=self.session.pk)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        # Students see slot-based picker; instructors/owners see datetime picker
        if self.user_role == "student":
            slots = InstructorAvailability.objects.filter(
                instructor=self.session.instructor,
                academy=self.get_academy(),
                is_active=True,
            )
            ctx = {
                "session": self.session,
                "slots": slots,
            }
            # Show remaining reschedules if a limit is set
            limit = self.get_academy().reschedule_limit
            if limit > 0:
                month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                reschedule_count = LiveSession.objects.filter(
                    academy=self.get_academy(),
                    rescheduled_from__isnull=False,
                    attendances__student=request.user,
                    created_at__gte=month_start,
                ).count()
                ctx["reschedules_remaining"] = limit - reschedule_count
            return render(request, "scheduling/reschedule_session_student.html", ctx)
        return render(request, "scheduling/reschedule_session.html", {
            "session": self.session,
        })

    def post(self, request, pk):
        from datetime import datetime, date as date_type

        # Student flow: slot + date based
        if self.user_role == "student":
            return self._handle_student_reschedule(request)

        # Instructor/Owner flow: free datetime picker
        new_start_str = request.POST.get("new_start")
        new_end_str = request.POST.get("new_end")
        reason = request.POST.get("reason", "").strip()

        try:
            new_start = timezone.make_aware(
                datetime.strptime(new_start_str, "%Y-%m-%dT%H:%M")
            )
            new_end = timezone.make_aware(
                datetime.strptime(new_end_str, "%Y-%m-%dT%H:%M")
            )
        except (ValueError, TypeError):
            return render(request, "scheduling/reschedule_session.html", {
                "session": self.session,
                "error": "Invalid date/time format.",
            })

        # Check overlap with other scheduled sessions for this instructor
        overlap = LiveSession.objects.filter(
            instructor=self.session.instructor,
            academy=self.get_academy(),
            status=LiveSession.SessionStatus.SCHEDULED,
            scheduled_start__lt=new_end,
            scheduled_end__gt=new_start,
        ).exclude(pk=self.session.pk).exists()

        if overlap:
            return render(request, "scheduling/reschedule_session.html", {
                "session": self.session,
                "error": "The new time overlaps with an existing session.",
            })

        return self._create_rescheduled_session(new_start, new_end, reason)

    def _handle_student_reschedule(self, request):
        """Student reschedule: picks from instructor's available slots."""
        from datetime import datetime, date as date_type

        slot = get_object_or_404(
            InstructorAvailability, pk=request.POST.get("slot"),
            academy=self.get_academy(),
        )
        session_date_str = request.POST.get("session_date")
        reason = request.POST.get("reason", "").strip()

        try:
            session_date = datetime.strptime(session_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return self._student_error("Invalid date format.")

        if session_date < date_type.today():
            return self._student_error("Cannot reschedule to a past date.")

        if session_date.weekday() != slot.day_of_week:
            return self._student_error(
                f"The selected date is not a {slot.get_day_of_week_display()}."
            )

        new_start = timezone.make_aware(
            datetime.combine(session_date, slot.start_time)
        )
        new_end = timezone.make_aware(
            datetime.combine(session_date, slot.end_time)
        )

        # Check overlap
        overlap = LiveSession.objects.filter(
            instructor=self.session.instructor,
            academy=self.get_academy(),
            status=LiveSession.SessionStatus.SCHEDULED,
            scheduled_start__lt=new_end,
            scheduled_end__gt=new_start,
        ).exclude(pk=self.session.pk).exists()

        if overlap:
            return self._student_error("This time slot is already booked.")

        return self._create_rescheduled_session(new_start, new_end, reason)

    def _student_error(self, error_msg):
        slots = InstructorAvailability.objects.filter(
            instructor=self.session.instructor,
            academy=self.get_academy(),
            is_active=True,
        )
        return render(self.request, "scheduling/reschedule_session_student.html", {
            "session": self.session,
            "slots": slots,
            "error": error_msg,
        })

    def _create_rescheduled_session(self, new_start, new_end, reason=""):
        """Shared logic: create new session, transfer attendances, mark old."""
        # Collect attendees before transferring (for notifications)
        old_attendees = list(
            SessionAttendance.objects.filter(session=self.session)
            .select_related("student")
            .values_list("student", flat=True)
        )

        new_session = LiveSession.objects.create(
            title=self.session.title,
            description=self.session.description,
            instructor=self.session.instructor,
            academy=self.get_academy(),
            course=self.session.course,
            scheduled_start=new_start,
            scheduled_end=new_end,
            duration_minutes=self.session.duration_minutes,
            session_type=self.session.session_type,
            max_participants=self.session.max_participants,
            room_name=generate_room_name(self.get_academy().slug, id(new_start)),
            rescheduled_from=self.session,
            status=LiveSession.SessionStatus.SCHEDULED,
        )

        # Transfer all attendances to new session
        SessionAttendance.objects.filter(session=self.session).update(session=new_session)

        # Mark old session as rescheduled
        self.session.status = LiveSession.SessionStatus.RESCHEDULED
        if reason:
            self.session.session_notes = (
                f"{self.session.session_notes}\nRescheduled: {reason}".strip()
            )
        self.session.save()

        # Reschedule notifications
        session_link = reverse("session-detail", args=[new_session.pk])
        date_str = new_start.strftime('%b %d, %Y')
        time_str = new_start.strftime('%H:%M')
        actor = self.request.user
        actor_name = actor.get_full_name() or actor.email

        # Notify all attendees (except the person who rescheduled)
        from apps.accounts.models import User
        for student_id in old_attendees:
            if student_id != actor.pk:
                Notification.objects.create(
                    recipient_id=student_id,
                    academy=self.get_academy(),
                    notification_type=Notification.NotificationType.SESSION_RESCHEDULED,
                    title="Session Rescheduled",
                    message=f"{self.session.title} has been rescheduled to {date_str} at {time_str}",
                    link=session_link,
                )

        # Notify instructor (if rescheduled by someone else)
        if self.session.instructor != actor:
            Notification.objects.create(
                recipient=self.session.instructor,
                academy=self.get_academy(),
                notification_type=Notification.NotificationType.SESSION_RESCHEDULED,
                title="Session Rescheduled",
                message=f"{actor_name} rescheduled {self.session.title} to {date_str} at {time_str}",
                link=session_link,
            )

        # Confirm to the person who rescheduled
        Notification.objects.create(
            recipient=actor,
            academy=self.get_academy(),
            notification_type=Notification.NotificationType.SESSION_RESCHEDULED,
            title="Reschedule Confirmed",
            message=f"{self.session.title} has been rescheduled to {date_str} at {time_str}",
            link=session_link,
        )

        return redirect("session-detail", pk=new_session.pk)


class StartRecordingView(TenantMixin, View):
    """Start recording a live session via LiveKit."""

    def post(self, request, pk):
        session = get_object_or_404(
            LiveSession, pk=pk, academy=self.get_academy()
        )
        try:
            egress_id = async_to_sync(self._start_recording)(session)
            session.recording_status = LiveSession.RecordingStatus.RECORDING
            session.save(update_fields=["recording_status"])
            cache.set(f"egress_{session.pk}", egress_id, timeout=7200)
            return JsonResponse({"status": "recording", "egress_id": egress_id})
        except Exception:
            session.recording_status = LiveSession.RecordingStatus.FAILED
            session.save(update_fields=["recording_status"])
            return JsonResponse({"status": "failed"}, status=500)

    async def _start_recording(self, session):
        """Override point for LiveKit recording start."""
        return None


class StopRecordingView(TenantMixin, View):
    """Stop recording a live session via LiveKit."""

    def post(self, request, pk):
        session = get_object_or_404(
            LiveSession, pk=pk, academy=self.get_academy()
        )
        egress_id = cache.get(f"egress_{session.pk}")
        try:
            async_to_sync(self._stop_recording)(egress_id)
            session.recording_status = LiveSession.RecordingStatus.PROCESSING
            session.save(update_fields=["recording_status"])
            return JsonResponse({"status": "processing"})
        except Exception:
            session.recording_status = LiveSession.RecordingStatus.FAILED
            session.save(update_fields=["recording_status"])
            return JsonResponse({"status": "failed"}, status=500)

    async def _stop_recording(self, egress_id):
        """Override point for LiveKit recording stop."""
        return None


class UpcomingSessionsPartialView(TenantMixin, ListView):
    model = LiveSession
    template_name = "scheduling/partials/_upcoming_sessions.html"
    context_object_name = "sessions"

    def get_queryset(self):
        return super().get_queryset().filter(
            scheduled_start__gte=timezone.now(),
            status="scheduled",
        ).select_related("instructor", "course")[:5]
