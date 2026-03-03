# FEAT-009: In-App Messaging System

**Status:** Planned
**Priority:** Medium
**Release:** 1
**Estimated Effort:** Large (8-12 hours)

---

## User Story

**As a** student or instructor within an academy,
**I want to** send and receive private messages to/from other members of my academy,
**So that** I can communicate about lessons, assignments, and scheduling without using external email or messaging tools.

---

## Acceptance Criteria

1. **AC-1:** A new `Message` model is created with fields: `sender`, `recipient`, `academy`, `subject`, `body`, `is_read`, `parent` (for threading), `created_at`.
2. **AC-2:** Users can access their inbox at `/notifications/messages/` showing received messages, sorted newest first.
3. **AC-3:** Users can compose a new message at `/notifications/messages/compose/` by selecting a recipient from the current academy's member list.
4. **AC-4:** Messages are scoped to the current academy -- users can only message members within the same academy.
5. **AC-5:** Clicking on a message in the inbox shows the full message thread (original + all replies).
6. **AC-6:** Users can reply to a message directly from the thread view.
7. **AC-7:** Unread message count is displayed in the sidebar navigation next to "Messages" menu item.
8. **AC-8:** Marking a message as read is automatic when the message thread is viewed. Manual mark-as-read/unread toggle is available via HTMX.
9. **AC-9:** The unread count badge updates without page reload via HTMX polling (every 30 seconds, similar to notifications).
10. **AC-10:** Sent messages are viewable in a "Sent" tab at `/notifications/messages/sent/`.

---

## Affected Files

| File | Action | Description |
|------|--------|-------------|
| `apps/notifications/models.py` | **Modify** | Add `Message` model |
| `apps/notifications/forms.py` | **Create** | Add `ComposeMessageForm` with recipient select, subject, body |
| `apps/notifications/views.py` | **Modify** | Add `InboxView`, `SentView`, `ComposeMessageView`, `MessageThreadView`, `ToggleReadView`, `UnreadCountPartialView` |
| `apps/notifications/urls.py` | **Modify** | Add URL patterns for messaging views |
| `templates/notifications/inbox.html` | **Create** | Inbox list page with unread indicators |
| `templates/notifications/sent.html` | **Create** | Sent messages list page |
| `templates/notifications/compose.html` | **Create** | Compose new message form |
| `templates/notifications/thread.html` | **Create** | Message thread view with reply form |
| `templates/notifications/partials/_message_row.html` | **Create** | HTMX partial for a single message row |
| `templates/notifications/partials/_unread_badge.html` | **Create** | HTMX partial for unread message count badge |
| `templates/base.html` | **Modify** | Add "Messages" link with unread count in sidebar navigation |
| `apps/notifications/admin.py` | **Modify** | Register `Message` model |
| `apps/notifications/migrations/XXXX_add_message.py` | **Auto-generated** | Migration for new model |

---

## UI Description

### Sidebar Navigation Addition (in `base.html`)
- New menu item below "Live Sessions" and above "My Progress":
  ```
  [Envelope icon] Messages  (3)
  ```
- The `(3)` is a DaisyUI badge: `badge badge-primary badge-sm` showing unread count
- Badge uses HTMX: `hx-get="/notifications/messages/unread-count/" hx-trigger="load, every 30s" hx-swap="innerHTML"`
- Badge is hidden when count is 0

### Inbox Page (`/notifications/messages/`)
- Page heading: "Messages" with tabs: **Inbox** | **Sent** | [Compose] button (right-aligned)
- Tab navigation using DaisyUI `tabs tabs-bordered`
- Message list in a table or card-based layout:
  ```
  [Unread dot]  From: {sender_name}    Subject: {subject}     {time_ago}
  [Unread dot]  From: {sender_name}    Subject: {subject}     {time_ago}
                From: {sender_name}    Subject: {subject}     {time_ago}  (read - no dot)
  ```
- Unread messages have a blue dot indicator and bold text
- Read messages have normal weight text
- Each row is clickable, navigating to the thread view
- Pagination: 20 messages per page
- Empty state: "No messages yet. [Compose a message]"

### Sent Page (`/notifications/messages/sent/`)
- Same layout as inbox but shows sent messages
- Columns: To: {recipient_name}, Subject, Date
- No unread indicators (all messages are "read" by sender)

### Compose Page (`/notifications/messages/compose/`)
- Card layout form:
  ```
  To:      [Select recipient dropdown - members of current academy]
  Subject: [Text input]
  Message: [Textarea, 6 rows]

  [Send Message] button
  ```
- Recipient dropdown: `select select-bordered w-full` populated with academy members
  - Sorted by role (owners first, then instructors, then students)
  - Display format: "First Last (role)" e.g., "Sarah Johnson (Instructor)"
  - Excludes the current user
- Subject: `input input-bordered w-full`
- Body: `textarea textarea-bordered w-full` with 6 rows
- "Send Message" button: `btn btn-primary`
- After sending, redirect to inbox with success message

### Thread View (`/notifications/messages/thread/<pk>/`)
- Shows the original message and all replies in chronological order
- Each message in the thread displayed as a chat-like bubble:
  ```
  [Avatar] Sender Name                                     {date}
  Subject (shown only on first message)
  Message body text...

  [Avatar] Other Person                                    {date}
  Reply body text...
  ```
- Reply form at the bottom:
  ```
  [Textarea, 3 rows]
  [Reply] button
  ```
- Reply form uses HTMX: `hx-post` to reply endpoint, appends new reply to thread without page reload
- On thread view load, mark all unread messages in the thread as read

---

## Implementation Details

### Model (`apps/notifications/models.py`)

```python
class Message(TimeStampedModel):
    sender = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="sent_direct_messages",
    )
    recipient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="received_messages",
    )
    academy = models.ForeignKey(
        "academies.Academy",
        on_delete=models.CASCADE,
        related_name="messages",
    )
    subject = models.CharField(max_length=300)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["sender", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.sender} -> {self.recipient}: {self.subject}"

    @property
    def thread_root(self):
        """Get the root message of this thread."""
        msg = self
        while msg.parent:
            msg = msg.parent
        return msg

    @property
    def thread_messages(self):
        """Get all messages in this thread, including self."""
        root = self.thread_root
        thread = [root] + list(
            Message.objects.filter(parent=root).order_by("created_at")
        )
        return thread
```

### Form (`apps/notifications/forms.py`)

```python
from django import forms
from apps.accounts.models import Membership, User
from .models import Message


class ComposeMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["recipient", "subject", "body"]

    def __init__(self, *args, academy=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if academy and user:
            # Get academy members excluding current user
            member_user_ids = Membership.objects.filter(
                academy=academy, is_active=True
            ).exclude(user=user).values_list("user_id", flat=True)
            self.fields["recipient"].queryset = User.objects.filter(
                id__in=member_user_ids
            ).order_by("first_name", "last_name")
            self.fields["recipient"].label_from_instance = (
                lambda u: f"{u.get_full_name() or u.email}"
            )
        self.fields["recipient"].widget.attrs["class"] = "select select-bordered w-full"
        self.fields["subject"].widget.attrs["class"] = "input input-bordered w-full"
        self.fields["body"].widget = forms.Textarea(
            attrs={"class": "textarea textarea-bordered w-full", "rows": 6}
        )


class ReplyMessageForm(forms.Form):
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "textarea textarea-bordered w-full",
            "rows": 3,
            "placeholder": "Type your reply...",
        })
    )
```

### Key Views (`apps/notifications/views.py`)

```python
class InboxView(TenantMixin, ListView):
    model = Message
    template_name = "notifications/inbox.html"
    context_object_name = "messages"
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(
            recipient=self.request.user,
            academy=self.get_academy(),
            parent__isnull=True,  # Only root messages
        ).select_related("sender")


class ComposeMessageView(TenantMixin, CreateView):
    model = Message
    form_class = ComposeMessageForm
    template_name = "notifications/compose.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["academy"] = self.get_academy()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        message = form.save(commit=False)
        message.sender = self.request.user
        message.academy = self.get_academy()
        message.save()
        return redirect("message-inbox")


class MessageThreadView(TenantMixin, DetailView):
    model = Message
    template_name = "notifications/thread.html"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return Message.objects.filter(
            academy=self.get_academy(),
        ).filter(
            models.Q(sender=self.request.user) | models.Q(recipient=self.request.user)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        root = self.object.thread_root
        ctx["thread"] = root.thread_messages
        ctx["reply_form"] = ReplyMessageForm()

        # Mark unread messages in thread as read
        Message.objects.filter(
            pk__in=[m.pk for m in ctx["thread"]],
            recipient=self.request.user,
            is_read=False,
        ).update(is_read=True)

        return ctx

    def post(self, request, pk):
        """Handle reply submission."""
        root_message = self.get_object().thread_root
        form = ReplyMessageForm(request.POST)
        if form.is_valid():
            # Determine the other party in the thread
            if root_message.sender == request.user:
                recipient = root_message.recipient
            else:
                recipient = root_message.sender

            Message.objects.create(
                sender=request.user,
                recipient=recipient,
                academy=self.get_academy(),
                subject=f"Re: {root_message.subject}",
                body=form.cleaned_data["body"],
                parent=root_message,
            )
        return redirect("message-thread", pk=root_message.pk)
```

### URL Configuration (`apps/notifications/urls.py`)

```python
# Add to existing urlpatterns:
path("messages/", views.InboxView.as_view(), name="message-inbox"),
path("messages/sent/", views.SentView.as_view(), name="message-sent"),
path("messages/compose/", views.ComposeMessageView.as_view(), name="message-compose"),
path("messages/<int:pk>/", views.MessageThreadView.as_view(), name="message-thread"),
path("messages/<int:pk>/toggle-read/", views.ToggleReadView.as_view(), name="message-toggle-read"),
path("messages/unread-count/", views.UnreadCountPartialView.as_view(), name="message-unread-count"),
```

---

## Edge Cases

1. **Messaging self:** The compose form excludes the current user from the recipient list, preventing self-messaging.
2. **Messaging across academies:** The `academy` FK on `Message` and the form's filtering of recipients to current academy members ensure messages are scoped within the academy.
3. **User removed from academy:** If a member is removed from an academy, their existing messages remain (for audit purposes). They can no longer send new messages to that academy's members because they cannot access the academy. The messages are only visible when the academy is active for the user.
4. **Very long threads:** For v1, all thread messages are loaded at once. For threads with >50 messages, this could be slow. Pagination within threads can be added in a future release.
5. **Concurrent reads:** Two users viewing the same thread simultaneously is fine -- each user's `is_read` status is tracked independently.
6. **Empty inbox:** Display a friendly empty state message with a CTA to compose a message.
7. **Recipient left academy:** If the recipient's membership is deactivated after a message is sent, the message remains in the inbox. The sender can still see it in their sent folder. No new replies can be sent to deactivated members (they will not appear in the recipient dropdown).
8. **HTML in message body:** Message body is rendered with Django's default auto-escaping (`{{ message.body }}`), so HTML tags are displayed as text, not executed. This prevents XSS. For v1, messages are plain text only. Rich text messaging can be added in a future release.
9. **Notification integration:** Optionally, create a `Notification` record when a new message is received (type: `general` or add a new `message` notification type). This ensures the notification badge also reflects new messages. Defer to FEAT-012 for signal-based integration.
10. **Thread with multiple participants:** The current design supports two-party threads only (sender + recipient). Group messaging is out of scope for v1. If a thread reply changes the recipient (e.g., forwarding), a new thread should be created.

---

## Dependencies

- **Internal:**
  - Depends on existing `Notification` model structure (for the `notifications` app).
  - Uses `TenantMixin` and `Membership` model for academy scoping and recipient filtering.
  - Uses `base.html` sidebar for navigation link.
- **External packages:** None new.
- **Migration:** Yes -- new migration for `Message` model.
- **Related features:**
  - FEAT-012 (Email Notifications) -- optionally send email notification when a new message is received.
  - The existing `ChatMessage` model in `notifications/models.py` is for real-time group chat (WebSocket). The new `Message` model is for private, asynchronous messaging. They serve different purposes and coexist.
- **Note on existing `ChatMessage` model:** The `ChatMessage` model already exists in `apps/notifications/models.py` for WebSocket-based group chat. The new `Message` model is distinct -- it is for private one-to-one messaging with inbox/sent/thread semantics. The naming is intentionally different to avoid confusion.

---

## Testing Notes

- Compose a message from one user to another within the same academy and verify it appears in the recipient's inbox.
- Verify the unread badge count updates in the sidebar.
- Open a message thread and verify it is automatically marked as read.
- Reply to a message and verify the reply appears in the thread.
- Toggle message read/unread status and verify the badge updates.
- Check the Sent folder and verify sent messages appear.
- Test with a user who has memberships in multiple academies -- messages should be scoped to the current academy only.
- Verify the recipient dropdown excludes the current user and only shows members of the current academy.
- Test pagination in the inbox with >20 messages.
- Test the empty state for a user with no messages.
