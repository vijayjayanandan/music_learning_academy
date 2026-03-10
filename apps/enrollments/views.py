import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView

logger = logging.getLogger(__name__)

from django.core.exceptions import ValidationError as DjangoValidationError

from apps.academies.mixins import TenantMixin
from apps.common.cache import invalidate_dashboard_cache
from apps.common.validators import validate_file_upload
from apps.courses.models import Course, Lesson
from .models import Enrollment, LessonProgress, AssignmentSubmission


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
        lesson_data = []
        for lesson in lessons:
            lp = progress_map.get(lesson.id)
            lesson_data.append({
                "lesson": lesson,
                "progress": lp,
                "is_completed": lp.is_completed if lp else False,
            })
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
                from django.contrib import messages
                names = ", ".join(c.title for c in missing)
                messages.error(request, f"You must complete these courses first: {names}")
                if request.htmx:
                    return render(request, "enrollments/partials/_enroll_button.html", {
                        "course": course, "enrollment": None, "prereq_missing": True,
                    })
                return redirect("course-detail", slug=slug)

        # FEAT-023: Redirect to payment for paid courses
        if not course.is_free:
            return redirect("checkout-course", course_slug=slug)

        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
            academy=self.get_academy(),
        )
        if created:
            invalidate_dashboard_cache(self.get_academy().pk)
        if request.htmx:
            return render(request, "enrollments/partials/_enroll_button.html", {
                "course": course, "enrollment": enrollment,
            })
        return redirect("course-detail", slug=slug)


class UnenrollView(TenantMixin, View):
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, academy=self.get_academy())
        Enrollment.objects.filter(
            student=request.user, course=course
        ).update(status="dropped")
        invalidate_dashboard_cache(self.get_academy().pk)
        if request.htmx:
            return render(request, "enrollments/partials/_enroll_button.html", {
                "course": course, "enrollment": None,
            })
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
            return render(request, "enrollments/partials/_lesson_progress_row.html", {
                "lesson": lesson,
                "progress": progress,
                "enrollment": enrollment,
            })
        return redirect("enrollment-detail", pk=pk)


class SubmitAssignmentView(TenantMixin, View):
    ALLOWED_FILE_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.txt',
        '.png', '.jpg', '.jpeg', '.gif',
    }
    ALLOWED_RECORDING_EXTENSIONS = {
        '.mp3', '.wav', '.ogg', '.flac', '.m4a',
        '.mp4', '.webm', '.mov',
    }
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    MAX_RECORDING_SIZE = 100 * 1024 * 1024  # 100MB

    def post(self, request, pk, assignment_pk):
        from apps.courses.models import PracticeAssignment

        enrollment = get_object_or_404(
            Enrollment, pk=pk, student=request.user, academy=self.get_academy()
        )
        # Security: ensure assignment belongs to the same academy (tenant isolation)
        assignment = get_object_or_404(
            PracticeAssignment, pk=assignment_pk, academy=self.get_academy()
        )

        # Security: validate practice_time_minutes is a reasonable integer
        try:
            practice_time = max(0, min(int(request.POST.get("practice_time_minutes", 0)), 1440))
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
                validate_file_upload(uploaded, self.ALLOWED_FILE_EXTENSIONS, self.MAX_FILE_SIZE)
                submission.file_upload = uploaded
                submission.save()
            except DjangoValidationError:
                pass  # silently skip invalid files

        if request.FILES.get("recording"):
            recording = request.FILES["recording"]
            try:
                validate_file_upload(recording, self.ALLOWED_RECORDING_EXTENSIONS, self.MAX_RECORDING_SIZE)
                submission.recording = recording
                submission.save()
            except DjangoValidationError:
                pass  # silently skip invalid files

        if request.htmx:
            return render(request, "enrollments/partials/_submission_status.html", {
                "submission": submission,
            })
        return redirect("enrollment-detail", pk=pk)


class CertificateView(TenantMixin, View):
    def get(self, request, pk):
        # Security: filter by academy too (tenant isolation)
        enrollment = get_object_or_404(
            Enrollment, pk=pk, student=request.user, status="completed",
            academy=self.get_academy()
        )
        return render(request, "enrollments/certificate.html", {
            "enrollment": enrollment,
            "course": enrollment.course,
            "student": enrollment.student,
        })


class CertificatePDFView(TenantMixin, View):
    """PROD-007: Download certificate as PDF."""

    def get(self, request, pk):
        from io import BytesIO
        from xhtml2pdf import pisa

        enrollment = get_object_or_404(
            Enrollment, pk=pk, student=request.user, status="completed",
            academy=self.get_academy()
        )
        html = render(request, "enrollments/certificate.html", {
            "enrollment": enrollment,
            "course": enrollment.course,
            "student": enrollment.student,
            "pdf_mode": True,
        }).content.decode("utf-8")

        buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=buffer)
        if pisa_status.err:
            logger.error("PDF generation failed for certificate %s", pk)
            return HttpResponse("PDF generation failed", status=500)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        slug = enrollment.course.slug
        response["Content-Disposition"] = f'attachment; filename="certificate-{slug}.pdf"'
        return response
