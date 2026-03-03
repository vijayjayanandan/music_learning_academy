from django import forms
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.views.generic import ListView

from apps.academies.mixins import TenantMixin
from apps.accounts.models import Membership
from .models import Message, Notification


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


# === Messaging Views ===

class InboxView(TenantMixin, ListView):
    model = Message
    template_name = "notifications/inbox.html"
    context_object_name = "messages_list"
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(
            recipient=self.request.user,
            academy=self.get_academy(),
            parent__isnull=True,
        ).select_related("sender")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["unread_msg_count"] = Message.objects.filter(
            recipient=self.request.user,
            academy=self.get_academy(),
            is_read=False,
        ).count()
        ctx["tab"] = "inbox"
        return ctx


class SentView(TenantMixin, ListView):
    model = Message
    template_name = "notifications/inbox.html"
    context_object_name = "messages_list"
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(
            sender=self.request.user,
            academy=self.get_academy(),
            parent__isnull=True,
        ).select_related("recipient")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tab"] = "sent"
        return ctx


class ComposeMessageView(TenantMixin, View):
    def get(self, request):
        academy = self.get_academy()
        members = Membership.objects.filter(
            academy=academy,
        ).exclude(user=request.user).select_related("user")
        return render(request, "notifications/compose.html", {
            "members": members,
            "reply_to": request.GET.get("reply_to"),
            "recipient_id": request.GET.get("to"),
        })

    def post(self, request):
        academy = self.get_academy()
        from apps.accounts.models import User
        recipient = get_object_or_404(User, pk=request.POST.get("recipient"))
        parent_id = request.POST.get("parent")
        parent = Message.objects.filter(pk=parent_id).first() if parent_id else None
        Message.objects.create(
            sender=request.user,
            recipient=recipient,
            academy=academy,
            subject=request.POST.get("subject", ""),
            body=request.POST.get("body", ""),
            parent=parent,
        )
        return redirect("message-inbox")


class MessageThreadView(TenantMixin, View):
    def get(self, request, pk):
        message = get_object_or_404(Message, pk=pk)
        root = message.thread_root
        thread = Message.objects.filter(
            Q(pk=root.pk) | Q(parent=root)
        ).select_related("sender", "recipient").order_by("created_at")
        # Mark as read
        thread.filter(recipient=request.user, is_read=False).update(is_read=True)
        academy = self.get_academy()
        return render(request, "notifications/thread.html", {
            "thread": thread,
            "root_message": root,
        })


class CourseChatView(TenantMixin, View):
    """FEAT-022: Group chat per course."""

    def get(self, request, slug):
        from apps.courses.models import Course
        from .models import ChatMessage

        course = get_object_or_404(Course, slug=slug, academy=self.get_academy())
        messages = ChatMessage.objects.filter(
            academy=self.get_academy(),
        ).select_related("sender").order_by("-created_at")[:50]
        return render(request, "notifications/chat_room.html", {
            "course": course,
            "chat_messages": reversed(list(messages)),
        })

    def post(self, request, slug):
        from apps.courses.models import Course
        from .models import ChatMessage

        course = get_object_or_404(Course, slug=slug, academy=self.get_academy())
        body = request.POST.get("message", "").strip()
        if body:
            ChatMessage.objects.create(
                academy=self.get_academy(),
                sender=request.user,
                message=body,
            )
        if request.htmx:
            messages = ChatMessage.objects.filter(
                academy=self.get_academy(),
            ).select_related("sender").order_by("-created_at")[:50]
            return render(request, "notifications/partials/_chat_messages.html", {
                "chat_messages": reversed(list(messages)),
            })
        return redirect("course-chat", slug=slug)


class UnreadMessageCountView(TenantMixin, View):
    def get(self, request):
        count = Message.objects.filter(
            recipient=request.user,
            academy=self.get_academy(),
            is_read=False,
        ).count()
        return render(request, "notifications/partials/_unread_badge.html", {
            "unread_msg_count": count,
        })
