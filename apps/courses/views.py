from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from apps.academies.mixins import TenantMixin
from apps.accounts.decorators import role_required
from apps.enrollments.models import Enrollment
from .forms import CourseForm, LessonForm, LessonAttachmentForm, PracticeAssignmentForm
from .models import Course, Lesson, LessonAttachment, PracticeAssignment


class CourseListView(TenantMixin, ListView):
    model = Course
    template_name = "courses/list.html"
    context_object_name = "courses"
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset().select_related("instructor")
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

    def form_valid(self, form):
        course = form.save(commit=False)
        course.academy = self.get_academy()
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
        return redirect("course-detail", slug=course.slug)


class CourseDetailView(TenantMixin, DetailView):
    model = Course
    template_name = "courses/detail.html"
    slug_url_kwarg = "slug"

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

    def get_success_url(self):
        return reverse("course-detail", kwargs={"slug": self.object.slug})


class CourseDeleteView(TenantMixin, View):
    def post(self, request, slug):
        course = get_object_or_404(
            Course, slug=slug, academy=self.get_academy()
        )
        course.delete()
        return redirect("course-list")

    def get_academy(self):
        academy = self.request.academy
        if not academy:
            from django.http import Http404
            raise Http404("No academy selected")
        return academy


class LessonCreateView(TenantMixin, View):
    def post(self, request, slug):
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
        return ctx


class LessonEditView(TenantMixin, View):
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
        return redirect("course-detail", slug=slug)


class LessonDeleteView(TenantMixin, View):
    def post(self, request, slug, pk):
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
        lesson = get_object_or_404(Lesson, pk=pk, academy=self.get_academy())
        form = LessonAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
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


class AttachmentDeleteView(TenantMixin, View):
    def post(self, request, slug, pk, attachment_pk):
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
