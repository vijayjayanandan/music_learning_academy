from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView

from apps.academies.mixins import TenantMixin
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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lessons = self.object.course.lessons.all()
        progress_map = {
            lp.lesson_id: lp
            for lp in self.object.lesson_progress.all()
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
        return ctx


class EnrollView(TenantMixin, View):
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, academy=self.get_academy())
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
            academy=self.get_academy(),
        )
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
        if request.htmx:
            return render(request, "enrollments/partials/_enroll_button.html", {
                "course": course, "enrollment": None,
            })
        return redirect("course-detail", slug=slug)


class MarkLessonCompleteView(TenantMixin, View):
    def post(self, request, pk, lesson_pk):
        enrollment = get_object_or_404(
            Enrollment, pk=pk, student=request.user
        )
        lesson = get_object_or_404(Lesson, pk=lesson_pk)
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
    def post(self, request, pk, assignment_pk):
        from apps.courses.models import PracticeAssignment

        enrollment = get_object_or_404(
            Enrollment, pk=pk, student=request.user
        )
        assignment = get_object_or_404(PracticeAssignment, pk=assignment_pk)

        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            student=request.user,
            academy=self.get_academy(),
            text_response=request.POST.get("text_response", ""),
            practice_time_minutes=int(request.POST.get("practice_time_minutes", 0)),
        )

        if request.FILES.get("file_upload"):
            submission.file_upload = request.FILES["file_upload"]
            submission.save()

        if request.FILES.get("recording"):
            recording = request.FILES["recording"]
            max_size = 100 * 1024 * 1024  # 100MB
            if recording.size <= max_size:
                submission.recording = recording
                submission.save()

        if request.htmx:
            return render(request, "enrollments/partials/_submission_status.html", {
                "submission": submission,
            })
        return redirect("enrollment-detail", pk=pk)
