from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from apps.academies.mixins import TenantMixin
from .models import LibraryResource


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

    def get(self, request):
        return render(request, "library/upload.html", {
            "resource_types": LibraryResource.ResourceType.choices,
        })

    def post(self, request):
        if request.FILES.get("file"):
            LibraryResource.objects.create(
                academy=self.get_academy(),
                uploaded_by=request.user,
                title=request.POST.get("title", "Untitled"),
                description=request.POST.get("description", ""),
                resource_type=request.POST.get("resource_type", "other"),
                file=request.FILES["file"],
                instrument=request.POST.get("instrument", ""),
                genre=request.POST.get("genre", ""),
                difficulty_level=request.POST.get("difficulty_level", ""),
            )
        return redirect("library-list")


class LibraryDetailView(TenantMixin, View):
    """View resource details and download."""

    def get(self, request, pk):
        resource = get_object_or_404(
            LibraryResource, pk=pk, academy=self.get_academy(),
        )
        resource.download_count += 1
        resource.save(update_fields=["download_count"])
        return render(request, "library/detail.html", {"resource": resource})


class LibraryDeleteView(TenantMixin, View):
    """Delete a resource (owner/instructor only)."""

    def post(self, request, pk):
        resource = get_object_or_404(
            LibraryResource, pk=pk, academy=self.get_academy(),
        )
        resource.delete()
        return redirect("library-list")
