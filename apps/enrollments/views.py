import logging

from django.contrib import messages
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView

from apps.academies.mixins import TenantMixin
from apps.common.cache import invalidate_dashboard_cache
from apps.common.validators import validate_file_upload
from apps.courses.models import Course, Lesson
from .models import Enrollment, LessonProgress, AssignmentSubmission

logger = logging.getLogger(__name__)


class MyEnrollmentsView(TenantMixin, ListView):
    model = Enrollment
    template_name = "enrollments/list.html"
    context_object_name = "enrollments"

    def get_queryset(self):
        return Enrollment.objects.filter(
            student=self.request.user,
            academy=self.get_academy(),
        ).select_related("course", "course__instructor")


class EnrollmentDetailView(TenantMixin, DetailView):
    model = Enrollment
    template_name = "enrollments/detail.html"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        # Security: users can only view their own enrollments (IDOR prevention)
        return Enrollment.objects.filter(
            student=self.request.user,
            academy=self.get_academy(),
        ).select_related("course", "course__instructor")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lessons = self.object.course.lessons.all()
        progress_map = {
            lp.lesson_id: lp
            for lp in self.object.lesson_progress.select_related("lesson").all()
        }

        # Build a map of lesson_id -> latest submission status
        # A lesson's submission status comes from its assignments' submissions by this student
        submission_status_map = {}
        submissions = (
            AssignmentSubmission.objects.filter(
                student=self.request.user,
                assignment__lesson__course=self.object.course,
                academy=self.get_academy(),
            )
            .select_related("assignment__lesson")
            .order_by("-created_at")
        )
        for sub in submissions:
            lesson_id = sub.assignment.lesson_id
            # Keep the first (most recent) submission status per lesson
            if lesson_id not in submission_status_map:
                submission_status_map[lesson_id] = sub.status

        lesson_data = []
        for lesson in lessons:
            lp = progress_map.get(lesson.id)
            is_completed = lp.is_completed if lp else False
            sub_status = submission_status_map.get(lesson.id)

            # Determine the display status badge
            if is_completed:
                status_badge = "Complete"
                status_class = "badge-success"
            elif sub_status == "needs_revision":
                status_badge = "Needs Revision"
                status_class = "badge-warning"
            elif sub_status == "reviewed":
                status_badge = "Reviewed"
                status_class = "badge-info"
            elif sub_status == "submitted":
                status_badge = "Submitted"
                status_class = "badge-accent"
            else:
                status_badge = "Not started"
                status_class = "badge-ghost"

            lesson_data.append(
                {
                    "lesson": lesson,
                    "progress": lp,
                    "is_completed": is_completed,
                    "status_badge": status_badge,
                    "status_class": status_class,
                }
            )
        ctx["lesson_data"] = lesson_data
        ctx["progress_percent"] = self.object.progress_percent

        # Find the first incomplete lesson for the Start/Continue CTA card
        first_incomplete_lesson = None
        for item in lesson_data:
            if not item["is_completed"]:
                first_incomplete_lesson = item["lesson"]
                break
        ctx["first_incomplete_lesson"] = first_incomplete_lesson

        return ctx


class EnrollView(TenantMixin, View):
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, academy=self.get_academy())

        # FEAT-019: Check prerequisites
        prerequisites = course.prerequisite_courses.all()
        if prerequisites.exists():
            completed_courses = Enrollment.objects.filter(
                student=request.user,
                course__in=prerequisites,
                status="completed",
            ).values_list("course_id", flat=True)
            missing = prerequisites.exclude(pk__in=completed_courses)
            if missing.exists():
                names = ", ".join(c.title for c in missing)
                messages.error(
                    request, f"You must complete these courses first: {names}"
                )
                if request.htmx:
                    return render(
                        request,
                        "enrollments/partials/_enroll_button.html",
                        {
                            "course": course,
                            "enrollment": None,
                            "prereq_missing": True,
                        },
                    )
                return redirect("course-detail", slug=slug)

        # FEAT-023: Redirect to payment for paid courses
        if not course.is_free:
            return redirect("checkout-course", course_slug=slug)

        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
            academy=self.get_academy(),
        )

        # Redirect to the first lesson if one exists, otherwise fall back to course detail
        first_lesson = course.lessons.order_by("order").first()

        if created:
            invalidate_dashboard_cache(self.get_academy().pk)
            if first_lesson:
                messages.success(
                    request,
                    f"You're enrolled in {course.title}! Start with your first lesson.",
                )
            else:
                messages.success(
                    request,
                    f"You're enrolled in {course.title}! Your instructor will add lessons soon.",
                )
        if first_lesson:
            redirect_url = reverse(
                "lesson-detail", kwargs={"slug": slug, "pk": first_lesson.pk}
            )
        else:
            redirect_url = reverse("course-detail", kwargs={"slug": slug})

        if request.htmx:
            response = HttpResponse(status=204)
            response["HX-Redirect"] = redirect_url
            return response
        return redirect(redirect_url)


class UnenrollView(TenantMixin, View):
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, academy=self.get_academy())
        Enrollment.objects.filter(student=request.user, course=course).update(
            status="dropped"
        )
        invalidate_dashboard_cache(self.get_academy().pk)
        if request.htmx:
            return render(
                request,
                "enrollments/partials/_enroll_button.html",
                {
                    "course": course,
                    "enrollment": None,
                },
            )
        return redirect("course-detail", slug=slug)


class MarkLessonCompleteView(TenantMixin, View):
    def post(self, request, pk, lesson_pk):
        enrollment = get_object_or_404(
            Enrollment, pk=pk, student=request.user, academy=self.get_academy()
        )
        # Security: ensure lesson belongs to the same academy (tenant isolation)
        lesson = get_object_or_404(Lesson, pk=lesson_pk, academy=self.get_academy())
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            academy=self.get_academy(),
        )
        progress.is_completed = not progress.is_completed
        progress.completed_at = timezone.now() if progress.is_completed else None
        progress.save()

        if request.htmx:
            # When called from lesson detail page, return the lesson-complete section
            if request.GET.get("from") == "lesson":
                course = lesson.course
                all_lessons = list(course.lessons.order_by("order"))
                total_lessons = len(all_lessons)
                completed_count = LessonProgress.objects.filter(
                    enrollment=enrollment,
                    is_completed=True,
                ).count()
                # Find next lesson
                next_lesson = None
                for i, lsn in enumerate(all_lessons):
                    if lsn.pk == lesson.pk and i < total_lessons - 1:
                        next_lesson = all_lessons[i + 1]
                        break
                return render(
                    request,
                    "courses/partials/_lesson_complete_section.html",
                    {
                        "lesson": lesson,
                        "lesson_progress": progress,
                        "enrollment": enrollment,
                        "course": course,
                        "next_lesson": next_lesson,
                        "total_lessons": total_lessons,
                        "completed_count": completed_count,
                    },
                )
            return render(
                request,
                "enrollments/partials/_lesson_progress_row.html",
                {
                    "lesson": lesson,
                    "progress": progress,
                    "enrollment": enrollment,
                },
            )
        return redirect("enrollment-detail", pk=pk)


class SubmitAssignmentView(TenantMixin, View):
    ALLOWED_FILE_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
    }
    ALLOWED_RECORDING_EXTENSIONS = {
        ".mp3",
        ".wav",
        ".ogg",
        ".flac",
        ".m4a",
        ".mp4",
        ".webm",
        ".mov",
    }
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    MAX_RECORDING_SIZE = 100 * 1024 * 1024  # 100MB

    def post(self, request, pk, assignment_pk):
        from apps.courses.models import PracticeAssignment

        get_object_or_404(
            Enrollment, pk=pk, student=request.user, academy=self.get_academy()
        )
        # Security: ensure assignment belongs to the same academy (tenant isolation)
        assignment = get_object_or_404(
            PracticeAssignment, pk=assignment_pk, academy=self.get_academy()
        )

        # Security: validate practice_time_minutes is a reasonable integer
        try:
            practice_time = max(
                0, min(int(request.POST.get("practice_time_minutes", 0)), 1440)
            )
        except (ValueError, TypeError):
            practice_time = 0

        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            student=request.user,
            academy=self.get_academy(),
            text_response=request.POST.get("text_response", ""),
            practice_time_minutes=practice_time,
        )

        if request.FILES.get("file_upload"):
            uploaded = request.FILES["file_upload"]
            try:
                validate_file_upload(
                    uploaded, self.ALLOWED_FILE_EXTENSIONS, self.MAX_FILE_SIZE
                )
                submission.file_upload = uploaded
                submission.save()
            except DjangoValidationError:
                pass  # silently skip invalid files

        if request.FILES.get("recording"):
            recording = request.FILES["recording"]
            try:
                validate_file_upload(
                    recording,
                    self.ALLOWED_RECORDING_EXTENSIONS,
                    self.MAX_RECORDING_SIZE,
                )
                submission.recording = recording
                submission.save()
            except DjangoValidationError:
                pass  # silently skip invalid files

        if request.htmx:
            return render(
                request,
                "enrollments/partials/_submission_status.html",
                {
                    "submission": submission,
                },
            )
        return redirect("enrollment-detail", pk=pk)


class CertificateView(TenantMixin, View):
    def get(self, request, pk):
        # Security: filter by academy too (tenant isolation)
        enrollment = get_object_or_404(
            Enrollment,
            pk=pk,
            student=request.user,
            status="completed",
            academy=self.get_academy(),
        )
        return render(
            request,
            "enrollments/certificate.html",
            {
                "enrollment": enrollment,
                "course": enrollment.course,
                "student": enrollment.student,
            },
        )


class CertificatePDFView(TenantMixin, View):
    """PROD-007: Download certificate as PDF."""

    def get(self, request, pk):
        from io import BytesIO
        from xhtml2pdf import pisa

        enrollment = get_object_or_404(
            Enrollment,
            pk=pk,
            student=request.user,
            status="completed",
            academy=self.get_academy(),
        )
        html = render(
            request,
            "enrollments/certificate.html",
            {
                "enrollment": enrollment,
                "course": enrollment.course,
                "student": enrollment.student,
                "pdf_mode": True,
            },
        ).content.decode("utf-8")

        buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=buffer)
        if pisa_status.err:
            logger.error("PDF generation failed for certificate %s", pk)
            return HttpResponse("PDF generation failed", status=500)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        slug = enrollment.course.slug
        response["Content-Disposition"] = (
            f'attachment; filename="certificate-{slug}.pdf"'
        )
        return response
