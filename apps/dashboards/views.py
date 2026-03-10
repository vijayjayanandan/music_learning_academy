from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Exists, OuterRef
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from django.db.models import Sum

from apps.academies.mixins import TenantMixin
from apps.accounts.models import Invitation, Membership
from apps.common.audit import AuditEvent
from apps.courses.models import Course, PracticeAssignment
from apps.dashboards.analytics import (
    FunnelAnalytics,
    LearningAnalytics,
    RevenueAnalytics,
)
from apps.dashboards.forms import StudentOnboardingForm
from apps.enrollments.models import Enrollment, AssignmentSubmission
from apps.payments.models import Payment, PlatformSubscription, Subscription
from apps.scheduling.models import LiveSession


class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request):
        academy = request.user.current_academy
        if not academy:
            # Check if user has any academies
            first_membership = request.user.memberships.first()
            if first_membership:
                request.user.current_academy = first_membership.academy
                request.user.save(update_fields=["current_academy"])
                academy = first_membership.academy
            else:
                return render(request, "dashboards/no_academy.html")

        role = request.user.get_role_in(academy)
        if role == "owner":
            return redirect("admin-dashboard")
        elif role == "instructor":
            return redirect("instructor-dashboard")
        else:
            return redirect("student-dashboard")


class AdminDashboardView(TenantMixin, TemplateView):
    template_name = "dashboards/admin_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        # Security: only owners can access admin dashboard
        if hasattr(request, "academy") and request.academy:
            role = request.user.get_role_in(request.academy)
            if role != "owner":
                return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        academy = self.get_academy()

        # Cache aggregate stats for 5 minutes (tenant-scoped key)
        cache_key = f"admin_dashboard_stats_{academy.pk}"
        stats = cache.get(cache_key)
        if stats is None:
            stats = {
                "total_students": Membership.objects.filter(
                    academy=academy, role="student", is_active=True
                ).count(),
                "total_instructors": Membership.objects.filter(
                    academy=academy, role="instructor", is_active=True
                ).count(),
                "total_courses": Course.objects.filter(
                    academy=academy, is_published=True
                ).count(),
            }
            cache.set(cache_key, stats, 300)  # 5 minutes
        ctx.update(stats)

        ctx["upcoming_sessions"] = LiveSession.objects.filter(
            academy=academy,
            status="scheduled",
            scheduled_start__gte=timezone.now(),
        ).select_related("instructor", "course")[:5]
        ctx["recent_enrollments"] = (
            Enrollment.objects.filter(
                academy=academy,
            )
            .select_related("student", "course")
            .order_by("-enrolled_at")[:10]
        )

        # Priority CTA for admin dashboard
        ctx["priority_cta"] = _compute_owner_priority_cta(academy)

        # Alerts for admin dashboard (sorted by priority)
        ctx["alerts"] = _compute_admin_alerts(academy)

        # Setup checklist (show if not live)
        if academy.setup_status != "live":
            completed, total, pct = academy.setup_progress
            ctx["setup_checklist"] = {
                "completed": completed,
                "total": total,
                "pct": pct,
            }
        else:
            ctx["setup_checklist"] = None

        # Platform Subscription info
        try:
            platform_sub = academy.platform_subscription
            ctx["platform_subscription"] = platform_sub
        except PlatformSubscription.DoesNotExist:
            ctx["platform_subscription"] = None

        # Monthly revenue
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        revenue_cents = (
            Payment.objects.filter(
                academy=academy,
                status="completed",
                paid_at__gte=month_start,
            ).aggregate(total=Sum("amount_cents"))["total"]
            or 0
        )
        ctx["monthly_revenue_display"] = f"${revenue_cents / 100:,.2f}"

        # Active student subscriptions count
        ctx["active_subscriptions_count"] = Subscription.objects.filter(
            academy=academy,
            status="active",
        ).count()

        return ctx


def _compute_admin_alerts(academy):
    """Compute a list of alert dicts for the admin dashboard.

    Each alert has at minimum: title (str), priority (int).
    Lower priority number = more urgent.
    Alerts are sorted by priority ascending.
    """
    now = timezone.now()
    alerts = []

    # 1. Overdue submissions (priority 1) — submitted > 48h ago, not yet reviewed
    overdue_threshold = now - timedelta(hours=48)
    overdue_count = AssignmentSubmission.objects.filter(
        academy=academy,
        status="submitted",
        created_at__lte=overdue_threshold,
    ).count()
    if overdue_count > 0:
        alerts.append(
            {
                "title": f"{overdue_count} overdue submission(s)",
                "priority": 1,
                "type": "overdue",
                "count": overdue_count,
            }
        )

    # 2. Sessions starting soon (priority 3) — within next hour
    soon_threshold = now + timedelta(hours=1)
    soon_sessions = LiveSession.objects.filter(
        academy=academy,
        status="scheduled",
        scheduled_start__gte=now,
        scheduled_start__lte=soon_threshold,
    ).count()
    if soon_sessions > 0:
        alerts.append(
            {
                "title": f"{soon_sessions} session(s) starting soon",
                "priority": 3,
                "type": "session_soon",
                "count": soon_sessions,
            }
        )

    # 3. Cancelled sessions today (priority 4)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)
    cancelled_count = LiveSession.objects.filter(
        academy=academy,
        status="cancelled",
        scheduled_start__gte=today_start,
        scheduled_start__lt=tomorrow_start,
    ).count()
    if cancelled_count > 0:
        alerts.append(
            {
                "title": f"{cancelled_count} cancelled session(s) today",
                "priority": 4,
                "type": "cancelled",
                "count": cancelled_count,
            }
        )

    # 4. Pending invitations (priority 5) — not accepted, not expired
    pending_invites = Invitation.objects.filter(
        academy=academy,
        accepted=False,
        expires_at__gt=now,
    ).count()
    if pending_invites > 0:
        alerts.append(
            {
                "title": f"{pending_invites} pending invitation(s)",
                "priority": 5,
                "type": "invitation",
                "count": pending_invites,
            }
        )

    # Sort by priority (lower = more urgent)
    alerts.sort(key=lambda a: a["priority"])
    return alerts


def _compute_owner_priority_cta(academy):
    """Return a dict describing the single highest-priority CTA for an owner.

    Priority order:
    1. Overdue assignment reviews (submitted > 48 hours ago, not yet reviewed)
    Returns None if no action is needed (healthy academy).
    """
    now = timezone.now()
    overdue_threshold = now - timedelta(hours=48)

    # Check for overdue assignment reviews
    overdue_submissions = AssignmentSubmission.objects.filter(
        academy=academy,
        status="submitted",
        created_at__lte=overdue_threshold,
    ).count()

    if overdue_submissions > 0:
        return {
            "type": "student",
            "message": f"{overdue_submissions} submission(s) awaiting review for over 48 hours.",
        }

    return None


class OwnerAnalyticsView(TenantMixin, TemplateView):
    """Analytics dashboard for academy owners."""

    template_name = "dashboards/owner_analytics.html"

    ALLOWED_PERIODS = {7, 30, 90}

    def dispatch(self, request, *args, **kwargs):
        # Security: only owners can access analytics dashboard
        if hasattr(request, "academy") and request.academy:
            role = request.user.get_role_in(request.academy)
            if role != "owner":
                return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        academy = self.get_academy()

        # Parse and validate ?days= parameter
        try:
            days = int(self.request.GET.get("days", 30))
        except (ValueError, TypeError):
            days = 30
        if days not in self.ALLOWED_PERIODS:
            days = 30
        ctx["selected_days"] = days

        # Revenue metrics
        mrr = RevenueAnalytics.get_mrr(academy)
        arpu = RevenueAnalytics.get_arpu(academy)
        ctx["mrr"] = mrr
        ctx["mrr_display"] = f"${mrr / 100:,.2f}"
        ctx["arpu"] = arpu
        ctx["arpu_display"] = f"${arpu / 100:,.2f}"
        ctx["revenue_summary"] = RevenueAnalytics.get_revenue_summary(
            academy, days=days
        )
        ctx["revenue_trend"] = RevenueAnalytics.get_revenue_trend(academy, months=3)

        # Revenue by type display helper
        by_type = ctx["revenue_summary"].get("by_type", {})
        ctx["by_type_display"] = {k: f"${v / 100:,.2f}" for k, v in by_type.items()}

        # Funnel metrics
        ctx["funnel"] = FunnelAnalytics.get_funnel(academy, days=days)
        ctx["enrollment_breakdown"] = FunnelAnalytics.get_enrollment_breakdown(academy)

        # Learning quality metrics
        ctx["learning"] = LearningAnalytics.get_metrics(academy)

        # Data freshness
        ctx["data_freshness"] = timezone.now()

        return ctx


class InstructorDashboardView(TenantMixin, TemplateView):
    template_name = "dashboards/instructor_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        # Security: only instructors and owners can access instructor dashboard
        if hasattr(request, "academy") and request.academy:
            role = request.user.get_role_in(request.academy)
            if role not in ("owner", "instructor"):
                return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        academy = self.get_academy()
        user = self.request.user

        ctx["my_courses"] = Course.objects.filter(
            academy=academy, instructor=user
        ).prefetch_related("lessons")
        ctx["upcoming_sessions"] = LiveSession.objects.filter(
            academy=academy,
            instructor=user,
            status="scheduled",
            scheduled_start__gte=timezone.now(),
        ).select_related("course")[:5]
        ctx["pending_submissions"] = AssignmentSubmission.objects.filter(
            academy=academy,
            assignment__lesson__course__instructor=user,
            status="submitted",
        ).select_related("student", "assignment")[:10]
        return ctx


def _compute_student_priority_cta(user, academy):
    """Return a dict describing the single highest-priority CTA for a student.

    Priority order:
    1. Session starting within 30 minutes (or started up to 15 min ago)
    2. Assignment with "needs_revision" status
    3. Pending assignment due within 48 hours
    4. Continue learning (active enrollment with incomplete lessons)
    5. Browse courses (fallback)
    """
    now = timezone.now()

    # --- Priority 1: Imminent session ---
    upcoming_threshold = now + timedelta(minutes=30)
    imminent_session = (
        LiveSession.objects.filter(
            academy=academy,
            attendances__student=user,
            scheduled_start__lte=upcoming_threshold,
            scheduled_start__gte=now - timedelta(minutes=15),
            status="scheduled",
        )
        .select_related("course")
        .order_by("scheduled_start")
        .first()
    )
    if imminent_session:
        return {
            "type": "session",
            "title": "Join Session Now",
            "subtitle": f"Your session '{imminent_session.title}' starts soon",
            "url": reverse("session-detail", args=[imminent_session.pk]),
            "color": "accent",
            "icon": "video",
        }

    # --- Priority 2: Assignment needing revision ---
    revision_needed = (
        AssignmentSubmission.objects.filter(
            student=user,
            assignment__lesson__course__academy=academy,
            status="needs_revision",
        )
        .select_related("assignment__lesson__course")
        .first()
    )
    if revision_needed:
        # Find the enrollment for this course so we can link to it
        course = revision_needed.assignment.lesson.course
        enrollment = Enrollment.objects.filter(
            student=user, course=course, status="active"
        ).first()
        target_url = (
            reverse("enrollment-detail", args=[enrollment.pk])
            if enrollment
            else reverse("course-list")
        )
        return {
            "type": "revise",
            "title": "Revise & Resubmit",
            "subtitle": f"Your assignment '{revision_needed.assignment.title}' needs revision",
            "url": target_url,
            "color": "warning",
            "icon": "pencil",
        }

    # --- Priority 3: Pending assignment due within 48 hours ---
    due_threshold = now + timedelta(hours=48)
    enrolled_course_ids = Enrollment.objects.filter(
        academy=academy, student=user, status="active"
    ).values_list("course_id", flat=True)

    submitted_subquery = AssignmentSubmission.objects.filter(
        assignment=OuterRef("pk"), student=user
    )
    urgent_assignment = (
        PracticeAssignment.objects.filter(
            lesson__course_id__in=enrolled_course_ids,
            lesson__course__academy=academy,
            due_date__gte=now,
            due_date__lte=due_threshold,
        )
        .exclude(Exists(submitted_subquery))
        .select_related("lesson__course")
        .order_by("due_date")
        .first()
    )
    if urgent_assignment:
        course = urgent_assignment.lesson.course
        enrollment = Enrollment.objects.filter(
            student=user, course=course, status="active"
        ).first()
        target_url = (
            reverse("enrollment-detail", args=[enrollment.pk])
            if enrollment
            else reverse("course-list")
        )
        return {
            "type": "submit",
            "title": "Submit Assignment",
            "subtitle": f"'{urgent_assignment.title}' is due soon",
            "url": target_url,
            "color": "info",
            "icon": "document",
        }

    # --- Priority 4: Continue learning (active enrollment with incomplete lessons) ---
    active_enrollments = Enrollment.objects.filter(
        academy=academy, student=user, status="active"
    ).select_related("course")

    for enrollment in active_enrollments:
        total_lessons = enrollment.course.lessons.count()
        if total_lessons == 0:
            continue
        completed = enrollment.lesson_progress.filter(is_completed=True).count()
        if completed < total_lessons:
            return {
                "type": "continue",
                "title": "Continue Learning",
                "subtitle": f"Pick up where you left off in '{enrollment.course.title}'",
                "url": reverse("enrollment-detail", args=[enrollment.pk]),
                "color": "primary",
                "icon": "book",
            }

    # --- Priority 5: Browse courses (fallback) ---
    return {
        "type": "browse",
        "title": "Browse Courses",
        "subtitle": "Discover new courses to start learning",
        "url": reverse("course-list"),
        "color": "primary",
        "icon": "search",
    }


class StudentDashboardView(TenantMixin, TemplateView):
    template_name = "dashboards/student_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        academy = self.get_academy()
        user = self.request.user

        # Onboarding card: show if the student has not filled in preferences
        # and has not explicitly dismissed the card.
        membership = user.memberships.filter(academy=academy).first()
        if membership and membership.role == "student":
            needs_onboarding = (
                not membership.onboarding_skipped
                and not membership.learning_goal
                and membership.skill_level == "beginner"
                and not membership.instruments
            )
            ctx["needs_onboarding"] = needs_onboarding
            if needs_onboarding:
                ctx["onboarding_form"] = StudentOnboardingForm(academy=academy)
        else:
            ctx["needs_onboarding"] = False

        ctx["enrollments"] = Enrollment.objects.filter(
            academy=academy, student=user, status="active"
        ).select_related("course", "course__instructor")

        ctx["upcoming_sessions"] = LiveSession.objects.filter(
            academy=academy,
            status="scheduled",
            scheduled_start__gte=timezone.now(),
            attendances__student=user,
        ).select_related("instructor", "course")[:5]

        # Single query: pending assignments for enrolled courses, not yet submitted
        enrolled_course_ids = ctx["enrollments"].values_list("course_id", flat=True)
        submitted_subquery = AssignmentSubmission.objects.filter(
            assignment=OuterRef("pk"), student=user
        )
        ctx["pending_assignments"] = list(
            PracticeAssignment.objects.filter(
                lesson__course_id__in=enrolled_course_ids,
                lesson__course__academy=academy,
                due_date__gte=timezone.now(),
            )
            .exclude(Exists(submitted_subquery))
            .select_related("lesson", "lesson__course")
        )

        # Single highest-priority CTA for the student
        ctx["priority_cta"] = _compute_student_priority_cta(user, academy)

        # "Continue where you left off" — find the most recent active enrollment
        # with an incomplete lesson and provide structured data for the template.
        continue_learning = None
        for enrollment in ctx["enrollments"]:
            lessons = list(enrollment.course.lessons.order_by("order"))
            if not lessons:
                continue
            completed_ids = set(
                enrollment.lesson_progress.filter(is_completed=True).values_list(
                    "lesson_id", flat=True
                )
            )
            first_incomplete = None
            for lesson in lessons:
                if lesson.pk not in completed_ids:
                    first_incomplete = lesson
                    break
            if first_incomplete:
                continue_learning = {
                    "course_title": enrollment.course.title,
                    "lesson_title": first_incomplete.title,
                    "progress_percent": enrollment.progress_percent,
                    "lesson_url": reverse(
                        "lesson-detail",
                        kwargs={
                            "slug": enrollment.course.slug,
                            "pk": first_incomplete.pk,
                        },
                    ),
                }
                break  # Use the first enrollment that has incomplete work
        ctx["continue_learning"] = continue_learning

        return ctx


class AuditLogView(LoginRequiredMixin, TemplateView):
    template_name = "dashboards/audit_log.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request, "academy") or not request.academy:
            return redirect("dashboard")
        role = request.user.get_role_in(request.academy)
        if role != "owner":
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["audit_events"] = AuditEvent.objects.filter(
            academy=self.request.academy
        ).select_related("actor")[:100]
        return ctx


class DashboardStatsPartialView(TenantMixin, View):
    def get(self, request):
        academy = self.get_academy()
        role = request.user.get_role_in(academy)
        ctx = {"current_academy": academy, "user_role": role}

        if role == "owner":
            cache_key = f"stats_partial_owner_{academy.pk}"
            stats = cache.get(cache_key)
            if stats is None:
                stats = {
                    "total_students": Membership.objects.filter(
                        academy=academy, role="student", is_active=True
                    ).count(),
                    "total_instructors": Membership.objects.filter(
                        academy=academy, role="instructor", is_active=True
                    ).count(),
                    "total_courses": Course.objects.filter(
                        academy=academy, is_published=True
                    ).count(),
                }
                cache.set(cache_key, stats, 30)  # 30 seconds
            ctx.update(stats)
        elif role == "instructor":
            cache_key = f"stats_partial_instructor_{academy.pk}_{request.user.pk}"
            stats = cache.get(cache_key)
            if stats is None:
                stats = {
                    "my_course_count": Course.objects.filter(
                        academy=academy, instructor=request.user
                    ).count(),
                    "pending_reviews": AssignmentSubmission.objects.filter(
                        academy=academy,
                        assignment__lesson__course__instructor=request.user,
                        status="submitted",
                    ).count(),
                }
                cache.set(cache_key, stats, 30)  # 30 seconds
            ctx.update(stats)

        return render(request, "dashboards/partials/_stats_cards.html", ctx)


@login_required
@require_POST
def student_onboarding_submit(request):
    """Handle the student onboarding card — save preferences or skip."""
    academy = request.academy
    if not academy:
        return redirect("dashboard")

    membership = request.user.memberships.filter(academy=academy).first()
    if not membership or membership.role != "student":
        return redirect("dashboard")

    action = request.POST.get("action")
    if action == "skip":
        membership.onboarding_skipped = True
        membership.save(update_fields=["onboarding_skipped"])
    else:
        form = StudentOnboardingForm(request.POST, academy=academy)
        if form.is_valid():
            if form.cleaned_data.get("skill_level"):
                membership.skill_level = form.cleaned_data["skill_level"]
            if form.cleaned_data.get("learning_goal"):
                membership.learning_goal = form.cleaned_data["learning_goal"]
            if form.cleaned_data.get("instruments"):
                membership.instruments = form.cleaned_data["instruments"]
            if form.cleaned_data.get("timezone"):
                request.user.timezone = form.cleaned_data["timezone"]
                request.user.save(update_fields=["timezone"])
            membership.onboarding_skipped = True  # Don't show again after completing
            membership.save()
            messages.success(request, "Welcome! Your preferences have been saved.")

    return redirect("student-dashboard")
