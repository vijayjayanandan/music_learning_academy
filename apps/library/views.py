import os

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from apps.academies.mixins import TenantMixin
from .models import LibraryResource

ALLOWED_LIBRARY_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".rtf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".mp3",
    ".wav",
    ".ogg",
    ".flac",
    ".m4a",
    ".aac",
    ".mp4",
    ".webm",
    ".mov",
    ".mid",
    ".midi",
    ".musicxml",
    ".mxl",
    ".zip",
}
MAX_LIBRARY_FILE_SIZE = 100 * 1024 * 1024  # 100MB


class LibraryListView(TenantMixin, ListView):
    """FEAT-042: Content library - browse and search."""

    model = LibraryResource
    template_name = "library/list.html"
    context_object_name = "resources"
    paginate_by = 20

    def get_queryset(self):
        qs = LibraryResource.objects.filter(academy=self.get_academy())
        resource_type = self.request.GET.get("type")
        instrument = self.request.GET.get("instrument")
        search = self.request.GET.get("q")
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        if instrument:
            qs = qs.filter(instrument=instrument)
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["resource_types"] = LibraryResource.ResourceType.choices
        return ctx


class LibraryUploadView(TenantMixin, View):
    """Upload a resource to the library."""

    def dispatch(self, request, *args, **kwargs):
        # Security: only instructors and owners can upload library resources
        if hasattr(request, "academy") and request.academy:
            role = request.user.get_role_in(request.academy)
            if role not in ("owner", "instructor"):
                return HttpResponseForbidden(
                    "Only instructors and owners can upload library resources."
                )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(
            request,
            "library/upload.html",
            {
                "resource_types": LibraryResource.ResourceType.choices,
            },
        )

    def post(self, request):
        if request.FILES.get("file"):
            uploaded_file = request.FILES["file"]
            # Security: validate file extension and size
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_LIBRARY_EXTENSIONS:
                from django.contrib import messages

                messages.error(request, f"File type '{ext}' is not allowed.")
                return redirect("library-upload")
            if uploaded_file.size > MAX_LIBRARY_FILE_SIZE:
                from django.contrib import messages

                messages.error(request, "File exceeds the 100MB size limit.")
                return redirect("library-upload")
            LibraryResource.objects.create(
                academy=self.get_academy(),
                uploaded_by=request.user,
                title=request.POST.get("title", "Untitled"),
                description=request.POST.get("description", ""),
                resource_type=request.POST.get("resource_type", "other"),
                file=uploaded_file,
                instrument=request.POST.get("instrument", ""),
                genre=request.POST.get("genre", ""),
                difficulty_level=request.POST.get("difficulty_level", ""),
            )
        return redirect("library-list")


class LibraryDetailView(TenantMixin, View):
    """View resource details and download."""

    def get(self, request, pk):
        resource = get_object_or_404(
            LibraryResource,
            pk=pk,
            academy=self.get_academy(),
        )
        resource.download_count += 1
        resource.save(update_fields=["download_count"])
        return render(request, "library/detail.html", {"resource": resource})


class LibraryDeleteView(TenantMixin, View):
    """Delete a resource (owner/instructor only)."""

    def post(self, request, pk):
        # Security: only owners and instructors can delete library resources
        role = request.user.get_role_in(self.get_academy())
        if role not in ("owner", "instructor"):
            return HttpResponseForbidden(
                "Only instructors and owners can delete library resources."
            )
        resource = get_object_or_404(
            LibraryResource,
            pk=pk,
            academy=self.get_academy(),
        )
        resource.delete()
        return redirect("library-list")
