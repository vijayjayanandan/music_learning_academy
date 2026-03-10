from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from django.core.exceptions import ValidationError as DjangoValidationError

from apps.academies.mixins import TenantMixin
from apps.accounts.decorators import role_required
from apps.common.cache import invalidate_dashboard_cache
from apps.common.validators import validate_file_upload
from apps.enrollments.models import Enrollment
from .forms import CourseForm, LessonForm, LessonAttachmentForm, PracticeAssignmentForm
from .models import Course, Lesson, LessonAttachment, PracticeAssignment


def _invalidate_dashboard_cache(academy_pk):
    """Clear cached dashboard stats when course data changes."""
    invalidate_dashboard_cache(academy_pk)


ALLOWED_ATTACHMENT_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.txt',
    '.png', '.jpg', '.jpeg', '.gif', '.svg',
    '.mp3', '.wav', '.ogg', '.flac', '.m4a',
    '.mp4', '.webm', '.mov',
    '.mid', '.midi', '.musicxml', '.mxl',
}
MAX_ATTACHMENT_SIZE = 50 * 1024 * 1024  # 50MB


def _check_instructor_or_owner(request, academy):
    """Return HttpResponseForbidden if user is not instructor or owner, else None."""
    role = request.user.get_role_in(academy)
    if role not in ("owner", "instructor"):
        return HttpResponseForbidden("Only instructors and owners can perform this action.")
    return None


class CourseListView(TenantMixin, ListView):
    model = Course
    template_name = "courses/list.html"
    context_object_name = "courses"
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset().select_related("instructor")

        # Students only see published courses
        academy = self.get_academy()
        role = self.request.user.get_role_in(academy)
        if role == "student":
            qs = qs.filter(is_published=True)

        q = self.request.GET.get("q")
        instrument = self.request.GET.get("instrument")
        difficulty = self.request.GET.get("difficulty")

        if q:
            qs = qs.filter(title__icontains=q)
        if instrument:
            qs = qs.filter(instrument__iexact=instrument)
        if difficulty:
            qs = qs.filter(difficulty_level=difficulty)

        return qs

    def get_template_names(self):
        if self.request.htmx:
            return ["courses/partials/_course_grid.html"]
        return [self.template_name]


class CourseCreateView(TenantMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = "courses/create.html"

    def dispatch(self, request, *args, **kwargs):
        # Security: only instructors and owners can create courses
        if hasattr(request, 'academy') and request.academy:
            denied = _check_instructor_or_owner(request, request.academy)
            if denied:
                return denied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        from apps.academies.models import check_course_limit
        academy = self.get_academy()
        is_allowed, current, max_count = check_course_limit(academy)
        if not is_allowed:
            form.add_error(None, f"This academy has reached its maximum of {max_count} courses.")
            return self.form_invalid(form)
        course = form.save(commit=False)
        course.academy = academy
        course.instructor = self.request.user
        course.slug = slugify(course.title)
        base_slug = course.slug
        counter = 1
        while Course.objects.filter(academy=course.academy, slug=course.slug).exists():
            course.slug = f"{base_slug}-{counter}"
            counter += 1
        if course.is_published:
            course.published_at = timezone.now()
        course.save()
        _invalidate_dashboard_cache(course.academy.pk)
        return redirect("course-detail", slug=course.slug)


class CourseDetailView(TenantMixin, DetailView):
    model = Course
    template_name = "courses/detail.html"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return super().get_queryset().select_related("instructor").prefetch_related(
            "lessons", "lessons__assignments", "lessons__attachments"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["lessons"] = self.object.lessons.all()
        ctx["lesson_form"] = LessonForm()
        ctx["enrollment"] = Enrollment.objects.filter(
            student=self.request.user, course=self.object
        ).first()
        ctx["is_instructor"] = self.object.instructor == self.request.user
        ctx["enrolled_count"] = self.object.enrolled_count
        return ctx


class CourseEditView(TenantMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = "courses/edit.html"
    slug_url_kwarg = "slug"

    def dispatch(self, request, *args, **kwargs):
        # Security: only the course instructor or academy owner can edit
        if hasattr(request, 'academy') and request.academy:
            denied = _check_instructor_or_owner(request, request.academy)
            if denied:
                return denied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        _invalidate_dashboard_cache(self.object.academy.pk)
        return response

    def get_success_url(self):
        return reverse("course-detail", kwargs={"slug": self.object.slug})


class CourseDeleteView(TenantMixin, View):
    def post(self, request, slug):
        # Security: only the course instructor or academy owner can delete
        denied = _check_instructor_or_owner(request, self.get_academy())
        if denied:
            return denied
        course = get_object_or_404(
            Course, slug=slug, academy=self.get_academy()
        )
        academy_pk = course.academy.pk
        course.delete()
        _invalidate_dashboard_cache(academy_pk)
        return redirect("course-list")


class LessonCreateView(TenantMixin, View):
    def post(self, request, slug):
        # Security: only instructors and owners can create lessons
        denied = _check_instructor_or_owner(request, self.get_academy())
        if denied:
            return denied
        course = get_object_or_404(Course, slug=slug, academy=self.get_academy())
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.academy = self.get_academy()
            if not lesson.order:
                last = course.lessons.order_by("-order").first()
                lesson.order = (last.order + 1) if last else 1
            lesson.save()
            if request.htmx:
                lessons = course.lessons.all()
                return render(request, "courses/partials/_lesson_list.html", {
                    "lessons": lessons, "course": course, "lesson_form": LessonForm(),
                })
        return redirect("course-detail", slug=slug)


class LessonDetailView(TenantMixin, DetailView):
    model = Lesson
    template_name = "courses/lesson_detail.html"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["course"] = self.object.course
        ctx["assignments"] = self.object.assignments.all()
        ctx["attachments"] = self.object.attachments.all()
        ctx["attachment_form"] = LessonAttachmentForm()
        ctx["assignment_form"] = PracticeAssignmentForm()
        ctx["is_instructor"] = (
            self.object.course.instructor == self.request.user
            or self.request.user.get_role_in(self.get_academy()) == "owner"
        )

        # Prev/next lesson navigation
        all_lessons = list(self.object.course.lessons.order_by("order"))
        total_lessons = len(all_lessons)
        ctx["total_lessons"] = total_lessons
        current_index = None
        for i, lesson in enumerate(all_lessons):
            if lesson.pk == self.object.pk:
                current_index = i
                break
        if current_index is not None:
            ctx["lesson_number"] = current_index + 1
            ctx["prev_lesson"] = all_lessons[current_index - 1] if current_index > 0 else None
            ctx["next_lesson"] = all_lessons[current_index + 1] if current_index < total_lessons - 1 else None
        else:
            ctx["lesson_number"] = 1
            ctx["prev_lesson"] = None
            ctx["next_lesson"] = None

        return ctx


class LessonEditView(TenantMixin, View):
    def dispatch(self, request, *args, **kwargs):
        # Security: only instructors and owners can edit lessons
        if hasattr(request, 'academy') and request.academy:
            denied = _check_instructor_or_owner(request, request.academy)
            if denied:
                return denied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, slug, pk):
        lesson = get_object_or_404(Lesson, pk=pk, academy=self.get_academy())
        form = LessonForm(instance=lesson)
        if request.htmx:
            return render(request, "courses/partials/_lesson_edit_form.html", {
                "form": form, "lesson": lesson, "course": lesson.course,
            })
        return render(request, "courses/lesson_edit.html", {
            "form": form, "lesson": lesson, "course": lesson.course,
        })

    def post(self, request, slug, pk):
        lesson = get_object_or_404(Lesson, pk=pk, academy=self.get_academy())
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            if request.htmx:
                return render(request, "courses/partials/_lesson_row.html", {
                    "lesson": lesson, "course": lesson.course,
                })
            return redirect("lesson-detail", slug=slug, pk=pk)
        return render(request, "courses/lesson_edit.html", {
            "form": form, "lesson": lesson, "course": lesson.course,
        })


class LessonDeleteView(TenantMixin, View):
    def post(self, request, slug, pk):
        # Security: only instructors and owners can delete lessons
        denied = _check_instructor_or_owner(request, self.get_academy())
        if denied:
            return denied
        lesson = get_object_or_404(Lesson, pk=pk, academy=self.get_academy())
        course = lesson.course
        lesson.delete()
        if request.htmx:
            lessons = course.lessons.all()
            return render(request, "courses/partials/_lesson_list.html", {
                "lessons": lessons, "course": course, "lesson_form": LessonForm(),
            })
        return redirect("course-detail", slug=slug)


class AttachmentUploadView(TenantMixin, View):
    def post(self, request, slug, pk):
        # Security: only instructors and owners can upload attachments
        denied = _check_instructor_or_owner(request, self.get_academy())
        if denied:
            return denied
        lesson = get_object_or_404(Lesson, pk=pk, academy=self.get_academy())
        form = LessonAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data.get("file")
            # Security: validate file extension, size, and MIME type
            if uploaded_file:
                try:
                    validate_file_upload(
                        uploaded_file,
                        allowed_extensions=ALLOWED_ATTACHMENT_EXTENSIONS,
                        max_size=MAX_ATTACHMENT_SIZE,
                    )
                except DjangoValidationError as e:
                    from django.contrib import messages
                    messages.error(request, e.message)
                    return redirect("lesson-detail", slug=slug, pk=pk)
            attachment = form.save(commit=False)
            attachment.lesson = lesson
            attachment.academy = self.get_academy()
            attachment.save()
            if request.htmx:
                return render(request, "courses/partials/_attachment_list.html", {
                    "attachments": lesson.attachments.all(),
                    "lesson": lesson,
                    "course": lesson.course,
                    "is_instructor": True,
                    "attachment_form": LessonAttachmentForm(),
                })
        return redirect("lesson-detail", slug=slug, pk=pk)


class AssignmentEditView(TenantMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if hasattr(request, 'academy') and request.academy:
            denied = _check_instructor_or_owner(request, request.academy)
            if denied:
                return denied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, slug, lesson_pk, pk):
        assignment = get_object_or_404(
            PracticeAssignment, pk=pk, academy=self.get_academy()
        )
        form = PracticeAssignmentForm(instance=assignment)
        return render(request, "courses/assignment_edit.html", {
            "form": form,
            "assignment": assignment,
            "lesson": assignment.lesson,
            "course": assignment.lesson.course,
        })

    def post(self, request, slug, lesson_pk, pk):
        assignment = get_object_or_404(
            PracticeAssignment, pk=pk, academy=self.get_academy()
        )
        form = PracticeAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            return redirect("lesson-detail", slug=slug, pk=lesson_pk)
        return render(request, "courses/assignment_edit.html", {
            "form": form,
            "assignment": assignment,
            "lesson": assignment.lesson,
            "course": assignment.lesson.course,
        })


class AssignmentDeleteView(TenantMixin, View):
    def post(self, request, slug, lesson_pk, pk):
        denied = _check_instructor_or_owner(request, self.get_academy())
        if denied:
            return denied
        assignment = get_object_or_404(
            PracticeAssignment, pk=pk, academy=self.get_academy()
        )
        assignment.delete()
        return redirect("lesson-detail", slug=slug, pk=lesson_pk)

class AttachmentDeleteView(TenantMixin, View):
    def post(self, request, slug, pk, attachment_pk):
        # Security: only instructors and owners can delete attachments
        denied = _check_instructor_or_owner(request, self.get_academy())
        if denied:
            return denied
        attachment = get_object_or_404(
            LessonAttachment, pk=attachment_pk, academy=self.get_academy()
        )
        lesson = attachment.lesson
        attachment.file.delete()
        attachment.delete()
        if request.htmx:
            return render(request, "courses/partials/_attachment_list.html", {
                "attachments": lesson.attachments.all(),
                "lesson": lesson,
                "course": lesson.course,
                "is_instructor": True,
                "attachment_form": LessonAttachmentForm(),
            })
        return redirect("lesson-detail", slug=slug, pk=pk)
