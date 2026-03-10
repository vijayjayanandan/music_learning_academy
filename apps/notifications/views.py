from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.views.generic import ListView

from apps.academies.mixins import TenantMixin
from apps.accounts.models import Membership, User
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
        # Security: filter by academy too (tenant isolation)
        notification = get_object_or_404(
            Notification, pk=pk, recipient=request.user, academy=self.get_academy()
        )
        notification.is_read = True
        notification.save()
        if request.htmx:
            return render(
                request,
                "notifications/partials/_notification_item.html",
                {
                    "notification": notification,
                },
            )
        return render(request, "notifications/list.html")


class MarkAllReadView(TenantMixin, View):
    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            academy=self.get_academy(),
            is_read=False,
        ).update(is_read=True)
        if request.htmx:
            return render(
                request,
                "notifications/partials/_notification_badge.html",
                {
                    "unread_count": 0,
                },
            )
        return render(request, "notifications/list.html")


class NotificationBadgePartialView(TenantMixin, View):
    def get(self, request):
        unread_count = Notification.objects.filter(
            recipient=request.user,
            academy=self.get_academy(),
            is_read=False,
        ).count()
        return render(
            request,
            "notifications/partials/_notification_badge.html",
            {
                "unread_count": unread_count,
            },
        )


# === Messaging Views ===


class InboxView(TenantMixin, View):
    """Unified conversation list (replaces separate inbox/sent tabs)."""

    def get(self, request):
        academy = self.get_academy()
        user = request.user
        roots = (
            Message.objects.filter(academy=academy, parent__isnull=True)
            .filter(Q(sender=user) | Q(recipient=user))
            .select_related("sender", "recipient")
        )
        conversations = []
        for root in roots:
            other_person = root.recipient if root.sender == user else root.sender
            replies = Message.objects.filter(parent=root).order_by("-created_at")
            last_message = replies.first() or root
            unread_count = Message.objects.filter(
                Q(pk=root.pk) | Q(parent=root),
                recipient=user,
                is_read=False,
            ).count()
            conversations.append(
                {
                    "root": root,
                    "other_person": other_person,
                    "last_message": last_message,
                    "unread_count": unread_count,
                }
            )
        conversations.sort(key=lambda c: c["last_message"].created_at, reverse=True)
        return render(
            request,
            "notifications/inbox.html",
            {
                "conversations": conversations,
            },
        )


class SentRedirectView(TenantMixin, View):
    """Backward compatibility — redirects to unified inbox."""

    def get(self, request):
        return redirect("message-inbox")


class ComposeMessageView(TenantMixin, View):
    def get(self, request):
        academy = self.get_academy()
        members = (
            Membership.objects.filter(
                academy=academy,
            )
            .exclude(user=request.user)
            .select_related("user")
        )
        return render(
            request,
            "notifications/compose.html",
            {
                "members": members,
                "reply_to": request.GET.get("reply_to"),
                "recipient_id": request.GET.get("to"),
            },
        )

    def post(self, request):
        academy = self.get_academy()
        from apps.accounts.models import User

        recipient = get_object_or_404(User, pk=request.POST.get("recipient"))
        # Security: verify recipient is a member of the same academy
        if not Membership.objects.filter(user=recipient, academy=academy).exists():
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Recipient is not a member of this academy.")
        # Security: prevent sending messages to yourself
        if recipient == request.user:
            from django.contrib import messages

            messages.error(request, "You cannot send a message to yourself.")
            return redirect("compose-message")
        parent_id = request.POST.get("parent")
        parent = None
        if parent_id:
            # Security: validate parent message belongs to this academy and involves the user
            parent = (
                Message.objects.filter(
                    pk=parent_id,
                    academy=academy,
                )
                .filter(Q(sender=request.user) | Q(recipient=request.user))
                .first()
            )
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
        academy = self.get_academy()
        # Security: only allow users who are sender or recipient to view the thread (IDOR prevention)
        message = get_object_or_404(Message, pk=pk, academy=academy)
        # Verify user is a participant in this message
        if message.sender != request.user and message.recipient != request.user:
            return HttpResponseForbidden(
                "You do not have permission to view this thread."
            )
        root = message.thread_root
        # Also verify the user is a participant in the root message
        if root.sender != request.user and root.recipient != request.user:
            return HttpResponseForbidden(
                "You do not have permission to view this thread."
            )
        other_person = root.recipient if root.sender == request.user else root.sender
        thread = (
            Message.objects.filter(Q(pk=root.pk) | Q(parent=root))
            .select_related("sender", "recipient")
            .order_by("created_at")
        )
        # Mark as read
        thread.filter(recipient=request.user, is_read=False).update(is_read=True)
        return render(
            request,
            "notifications/thread.html",
            {
                "thread": thread,
                "root_message": root,
                "other_person": other_person,
            },
        )

    def post(self, request, pk):
        academy = self.get_academy()
        root = get_object_or_404(Message, pk=pk, academy=academy, parent__isnull=True)
        if root.sender != request.user and root.recipient != request.user:
            return HttpResponseForbidden("Not authorized.")
        body = request.POST.get("body", "").strip()
        if not body:
            return HttpResponse(status=204)
        recipient = root.recipient if root.sender == request.user else root.sender
        new_msg = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            academy=academy,
            subject=f"Re: {root.subject}",
            body=body,
            parent=root,
        )
        if getattr(request, "htmx", False):
            return render(
                request, "notifications/partials/_chat_bubble.html", {"msg": new_msg}
            )
        return redirect("message-thread", pk=root.pk)


class ConversationWithView(TenantMixin, View):
    """One-click 'Message Instructor' — finds or creates a thread with target user."""

    def get(self, request, pk):
        academy = self.get_academy()
        target = get_object_or_404(User, pk=pk)
        # Security: prevent messaging yourself
        if target == request.user:
            return redirect("message-inbox")
        # Security: verify target is a member of the same academy
        if not Membership.objects.filter(user=target, academy=academy).exists():
            return HttpResponseForbidden("Target user is not a member of this academy.")
        # Find existing root thread between these two users
        existing = (
            Message.objects.filter(academy=academy, parent__isnull=True)
            .filter(
                Q(sender=request.user, recipient=target)
                | Q(sender=target, recipient=request.user)
            )
            .order_by("-created_at")
            .first()
        )
        if existing:
            return redirect("message-thread", pk=existing.pk)
        # Create new thread anchor
        root = Message.objects.create(
            sender=request.user,
            recipient=target,
            academy=academy,
            subject="Conversation",
            body="",
        )
        return redirect("message-thread", pk=root.pk)


class CourseChatView(TenantMixin, View):
    """FEAT-022: Group chat per course."""

    def get(self, request, slug):
        from apps.courses.models import Course
        from .models import ChatMessage

        course = get_object_or_404(Course, slug=slug, academy=self.get_academy())
        messages = (
            ChatMessage.objects.filter(
                academy=self.get_academy(),
            )
            .select_related("sender")
            .order_by("-created_at")[:50]
        )
        return render(
            request,
            "notifications/chat_room.html",
            {
                "course": course,
                "chat_messages": reversed(list(messages)),
            },
        )

    def post(self, request, slug):
        from apps.courses.models import Course
        from .models import ChatMessage

        get_object_or_404(Course, slug=slug, academy=self.get_academy())
        body = request.POST.get("message", "").strip()
        if body:
            ChatMessage.objects.create(
                academy=self.get_academy(),
                sender=request.user,
                message=body,
            )
        if request.htmx:
            messages = (
                ChatMessage.objects.filter(
                    academy=self.get_academy(),
                )
                .select_related("sender")
                .order_by("-created_at")[:50]
            )
            return render(
                request,
                "notifications/partials/_chat_messages.html",
                {
                    "chat_messages": reversed(list(messages)),
                },
            )
        return redirect("course-chat", slug=slug)


class UnreadMessageCountView(TenantMixin, View):
    def get(self, request):
        count = Message.objects.filter(
            recipient=request.user,
            academy=self.get_academy(),
            is_read=False,
        ).count()
        return render(
            request,
            "notifications/partials/_unread_badge.html",
            {
                "unread_msg_count": count,
            },
        )
