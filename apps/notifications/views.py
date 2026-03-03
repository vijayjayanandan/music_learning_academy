from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import ListView

from apps.academies.mixins import TenantMixin
from .models import Notification


class NotificationListView(TenantMixin, ListView):
    model = Notification
    template_name = "notifications/list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
            academy=self.get_academy(),
        )


class MarkReadView(TenantMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(
            Notification, pk=pk, recipient=request.user
        )
        notification.is_read = True
        notification.save()
        if request.htmx:
            return render(request, "notifications/partials/_notification_item.html", {
                "notification": notification,
            })
        return render(request, "notifications/list.html")


class MarkAllReadView(TenantMixin, View):
    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            academy=self.get_academy(),
            is_read=False,
        ).update(is_read=True)
        if request.htmx:
            return render(request, "notifications/partials/_notification_badge.html", {
                "unread_count": 0,
            })
        return render(request, "notifications/list.html")


class NotificationBadgePartialView(TenantMixin, View):
    def get(self, request):
        unread_count = Notification.objects.filter(
            recipient=request.user,
            academy=self.get_academy(),
            is_read=False,
        ).count()
        return render(request, "notifications/partials/_notification_badge.html", {
            "unread_count": unread_count,
        })
