from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.academies.mixins import TenantMixin
from apps.accounts.models import Membership
from apps.courses.models import Course
from apps.enrollments.models import Enrollment, AssignmentSubmission
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
                return redirect("academy-create")

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
        if hasattr(request, 'academy') and request.academy:
            role = request.user.get_role_in(request.academy)
            if role != "owner":
                return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        academy = self.get_academy()
        ctx["total_students"] = Membership.objects.filter(
            academy=academy, role="student", is_active=True
        ).count()
        ctx["total_instructors"] = Membership.objects.filter(
            academy=academy, role="instructor", is_active=True
        ).count()
        ctx["total_courses"] = Course.objects.filter(
            academy=academy, is_published=True
        ).count()
        ctx["upcoming_sessions"] = LiveSession.objects.filter(
            academy=academy,
            status="scheduled",
            scheduled_start__gte=timezone.now(),
        ).select_related("instructor", "course")[:5]
        ctx["recent_enrollments"] = Enrollment.objects.filter(
            academy=academy,
        ).select_related("student", "course").order_by("-enrolled_at")[:10]
        return ctx


class InstructorDashboardView(TenantMixin, TemplateView):
    template_name = "dashboards/instructor_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        # Security: only instructors and owners can access instructor dashboard
        if hasattr(request, 'academy') and request.academy:
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
        )
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


class StudentDashboardView(TenantMixin, TemplateView):
    template_name = "dashboards/student_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        academy = self.get_academy()
        user = self.request.user

        ctx["enrollments"] = Enrollment.objects.filter(
            academy=academy, student=user, status="active"
        ).select_related("course", "course__instructor")

        ctx["upcoming_sessions"] = LiveSession.objects.filter(
            academy=academy,
            status="scheduled",
            scheduled_start__gte=timezone.now(),
            attendances__student=user,
        ).select_related("instructor", "course")[:5]

        ctx["pending_assignments"] = []
        for enrollment in ctx["enrollments"]:
            for lesson in enrollment.course.lessons.all():
                for assignment in lesson.assignments.filter(due_date__gte=timezone.now()):
                    if not AssignmentSubmission.objects.filter(
                        assignment=assignment, student=user
                    ).exists():
                        ctx["pending_assignments"].append(assignment)

        return ctx


class DashboardStatsPartialView(TenantMixin, View):
    def get(self, request):
        academy = self.get_academy()
        role = request.user.get_role_in(academy)
        ctx = {"current_academy": academy, "user_role": role}

        if role == "owner":
            ctx["total_students"] = Membership.objects.filter(
                academy=academy, role="student", is_active=True
            ).count()
            ctx["total_instructors"] = Membership.objects.filter(
                academy=academy, role="instructor", is_active=True
            ).count()
            ctx["total_courses"] = Course.objects.filter(
                academy=academy, is_published=True
            ).count()
        elif role == "instructor":
            ctx["my_course_count"] = Course.objects.filter(
                academy=academy, instructor=request.user
            ).count()
            ctx["pending_reviews"] = AssignmentSubmission.objects.filter(
                academy=academy,
                assignment__lesson__course__instructor=request.user,
                status="submitted",
            ).count()

        return render(request, "dashboards/partials/_stats_cards.html", ctx)
