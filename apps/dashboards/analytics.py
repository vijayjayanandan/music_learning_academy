"""Analytics service layer for owner dashboard metrics.

Provides computed metrics from existing data models -- no schema changes needed.
Results are cached with tenant-scoped keys.
"""

from datetime import timedelta

from django.core.cache import cache
from django.db.models import Sum
from django.utils import timezone


class RevenueAnalytics:
    """Compute revenue metrics for an academy."""

    CACHE_TTL = 3600  # 1 hour

    @classmethod
    def get_mrr(cls, academy):
        """Monthly Recurring Revenue from active subscriptions.

        Normalizes quarterly/annual plans to monthly equivalent.
        Returns amount in cents.
        """
        cache_key = f"analytics_mrr_{academy.pk}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        from apps.payments.models import Subscription

        # Get all active subscriptions with their plans
        subs = Subscription.objects.filter(
            academy=academy,
            status__in=["active", "trialing"],
        ).select_related("plan")

        mrr_cents = 0
        for sub in subs:
            if sub.plan and sub.plan.price_cents:
                price = sub.plan.price_cents
                cycle = sub.plan.billing_cycle
                if cycle == "quarterly":
                    mrr_cents += price / 3
                elif cycle == "annual":
                    mrr_cents += price / 12
                else:  # monthly (default)
                    mrr_cents += price

        result = int(mrr_cents)
        cache.set(cache_key, result, cls.CACHE_TTL)
        return result

    @classmethod
    def get_arpu(cls, academy):
        """Average Revenue Per User (per active student) this month.

        Returns amount in cents.
        """
        from apps.accounts.models import Membership
        from apps.payments.models import Payment

        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        revenue = (
            Payment.objects.filter(
                academy=academy,
                status="completed",
                paid_at__gte=month_start,
            ).aggregate(total=Sum("amount_cents"))["total"]
            or 0
        )

        student_count = Membership.objects.filter(
            academy=academy, role="student", is_active=True
        ).count()

        if student_count == 0:
            return 0
        return int(revenue / student_count)

    @classmethod
    def get_revenue_summary(cls, academy, days=30):
        """Revenue summary for a given period.

        Returns dict with: total_cents, by_type, completed_count,
        refund_count, refund_rate, failed_count.
        """
        cache_key = f"analytics_revenue_{academy.pk}_{days}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        from apps.payments.models import Payment, Refund

        cutoff = timezone.now() - timedelta(days=days)

        payments = Payment.objects.filter(academy=academy, paid_at__gte=cutoff)

        completed = payments.filter(status="completed")
        total_cents = completed.aggregate(total=Sum("amount_cents"))["total"] or 0
        completed_count = completed.count()

        # Revenue by type
        by_type = {}
        for ptype in ["course", "subscription", "package"]:
            amt = (
                completed.filter(payment_type=ptype).aggregate(
                    total=Sum("amount_cents")
                )["total"]
                or 0
            )
            by_type[ptype] = amt

        # Refund metrics -- Refund extends TenantScopedModel so has direct academy FK
        refund_count = Refund.objects.filter(
            academy=academy,
            status="completed",
            created_at__gte=cutoff,
        ).count()

        refund_rate = 0
        if completed_count > 0:
            refund_rate = round((refund_count / completed_count) * 100, 1)

        # Failed payments
        failed_count = payments.filter(status="failed").count()

        result = {
            "total_cents": total_cents,
            "total_display": f"${total_cents / 100:,.2f}",
            "by_type": by_type,
            "completed_count": completed_count,
            "refund_count": refund_count,
            "refund_rate": refund_rate,
            "failed_count": failed_count,
        }
        cache.set(cache_key, result, cls.CACHE_TTL)
        return result

    @classmethod
    def get_revenue_trend(cls, academy, months=3):
        """Monthly revenue for the last N months.

        Returns list of dicts: [{month: 'Jan 2026', total_cents: 1500, display: '$15.00'}, ...]
        Uses calendar month boundaries for accurate grouping.
        """
        from apps.payments.models import Payment

        now = timezone.now()
        trend = []

        for i in range(months - 1, -1, -1):
            # Walk backwards from current month
            # Calculate the target month by subtracting i months
            year = now.year
            month = now.month - i

            # Handle year rollover when going backwards
            while month <= 0:
                month += 12
                year -= 1

            month_start = now.replace(
                year=year, month=month, day=1,
                hour=0, minute=0, second=0, microsecond=0,
            )

            # Calculate next month start
            if month == 12:
                next_month_start = month_start.replace(year=year + 1, month=1)
            else:
                next_month_start = month_start.replace(month=month + 1)

            total = (
                Payment.objects.filter(
                    academy=academy,
                    status="completed",
                    paid_at__gte=month_start,
                    paid_at__lt=next_month_start,
                ).aggregate(total=Sum("amount_cents"))["total"]
                or 0
            )

            trend.append(
                {
                    "month": month_start.strftime("%b %Y"),
                    "total_cents": total,
                    "display": f"${total / 100:,.2f}",
                }
            )
        return trend


class FunnelAnalytics:
    """Compute student acquisition funnel metrics."""

    CACHE_TTL = 300  # 5 minutes

    @classmethod
    def get_funnel(cls, academy, days=30):
        """Student acquisition funnel for a given period.

        Returns dict with counts and conversion rates for each stage:
        - members_joined: new student memberships created in the period
        - enrolled: new enrollments created in the period
        - started_learning: students who completed at least one lesson
        - retained_30d: enrollments still active 30+ days after creation
        """
        cache_key = f"analytics_funnel_{academy.pk}_{days}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        from apps.accounts.models import Membership
        from apps.enrollments.models import Enrollment, LessonProgress

        cutoff = timezone.now() - timedelta(days=days)

        # Stage 1: Members joined (Membership has joined_at from auto_now_add)
        members_joined = Membership.objects.filter(
            academy=academy,
            role="student",
            joined_at__gte=cutoff,
        ).count()

        # Stage 2: Enrolled in a course
        period_enrollments = Enrollment.objects.filter(
            academy=academy,
            enrolled_at__gte=cutoff,
        )
        enrolled = period_enrollments.count()

        # Stage 3: Started learning (has at least one LessonProgress record)
        enrolled_ids = period_enrollments.values_list("pk", flat=True)
        started_learning = (
            LessonProgress.objects.filter(
                enrollment__in=enrolled_ids,
            )
            .values("enrollment")
            .distinct()
            .count()
        )

        # Stage 4: Retained (enrolled 30+ days ago within the period, still active)
        retained_cutoff = timezone.now() - timedelta(days=30)
        retained = Enrollment.objects.filter(
            academy=academy,
            enrolled_at__gte=cutoff,
            enrolled_at__lte=retained_cutoff,
            status__in=["active", "completed"],
        ).count()

        # Compute conversion rates (safe division)
        def rate(numerator, denominator):
            if denominator == 0:
                return 0
            return round((numerator / denominator) * 100, 1)

        result = {
            "members_joined": members_joined,
            "enrolled": enrolled,
            "started_learning": started_learning,
            "retained_30d": retained,
            "join_to_enroll_rate": rate(enrolled, members_joined),
            "enroll_to_learn_rate": rate(started_learning, enrolled),
            "learn_to_retain_rate": rate(retained, started_learning),
            "period_days": days,
        }
        cache.set(cache_key, result, cls.CACHE_TTL)
        return result

    @classmethod
    def get_enrollment_breakdown(cls, academy):
        """Enrollment status breakdown.

        Returns dict with count per status: active, completed, dropped, paused, total.
        """
        from apps.enrollments.models import Enrollment

        breakdown = {}
        for status in ["active", "completed", "dropped", "paused"]:
            breakdown[status] = Enrollment.objects.filter(
                academy=academy,
                status=status,
            ).count()
        breakdown["total"] = sum(breakdown.values())
        return breakdown


class LearningAnalytics:
    """Compute learning quality metrics."""

    @classmethod
    def get_metrics(cls, academy):
        """Learning quality metrics.

        Returns dict with: avg_progress, completion_rate, total_reviewed,
        attendance_rate, no_show_rate, total_sessions_completed.
        """
        from apps.enrollments.models import AssignmentSubmission, Enrollment
        from apps.scheduling.models import LiveSession, SessionAttendance

        # --- Average enrollment progress ---
        active_enrollments = Enrollment.objects.filter(
            academy=academy, status="active"
        )
        enrollment_count = active_enrollments.count()

        if enrollment_count > 0:
            # Cap at 100 records to avoid excessive DB hits from progress_percent property
            # (each call triggers 2 queries: lessons count + completed count)
            sample = list(active_enrollments[:100])
            total_progress = sum(e.progress_percent for e in sample)
            avg_progress = round(total_progress / len(sample), 1)
        else:
            avg_progress = 0

        # --- Completion rate ---
        total_enrollments = Enrollment.objects.filter(academy=academy).count()
        completed_enrollments = Enrollment.objects.filter(
            academy=academy, status="completed"
        ).count()
        if total_enrollments > 0:
            completion_rate = round(
                (completed_enrollments / total_enrollments) * 100, 1
            )
        else:
            completion_rate = 0

        # --- Review count (submissions that have been reviewed) ---
        # AssignmentSubmission has academy FK from TenantScopedModel
        total_reviewed = AssignmentSubmission.objects.filter(
            academy=academy,
            status__in=["reviewed", "approved", "needs_revision"],
            reviewed_at__isnull=False,
        ).count()

        # --- Session attendance metrics ---
        completed_sessions = LiveSession.objects.filter(
            academy=academy,
            status="completed",
        )
        total_registrations = SessionAttendance.objects.filter(
            session__in=completed_sessions,
        ).count()
        attended = SessionAttendance.objects.filter(
            session__in=completed_sessions,
            status="attended",
        ).count()

        if total_registrations > 0:
            attendance_rate = round(
                (attended / total_registrations) * 100, 1
            )
        else:
            attendance_rate = 0

        no_show_count = SessionAttendance.objects.filter(
            session__in=completed_sessions,
            status="absent",
        ).count()
        if total_registrations > 0:
            no_show_rate = round(
                (no_show_count / total_registrations) * 100, 1
            )
        else:
            no_show_rate = 0

        return {
            "avg_progress": avg_progress,
            "completion_rate": completion_rate,
            "total_reviewed": total_reviewed,
            "attendance_rate": attendance_rate,
            "no_show_rate": no_show_rate,
            "total_sessions_completed": completed_sessions.count(),
        }
