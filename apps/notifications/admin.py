from django.contrib import admin
from .models import Notification, Message, ChatMessage


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "recipient",
        "academy",
        "notification_type",
        "is_read",
        "created_at",
    ]
    list_filter = ["notification_type", "is_read", "academy"]
    search_fields = ["title", "message", "recipient__email"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["recipient", "academy"]
    list_select_related = ["recipient", "academy"]
    date_hierarchy = "created_at"

    actions = ["mark_as_read", "mark_as_unread"]

    @admin.action(description="Mark selected notifications as read")
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notification(s) marked as read.")

    @admin.action(description="Mark selected notifications as unread")
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notification(s) marked as unread.")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        "subject",
        "sender",
        "recipient",
        "academy",
        "is_read",
        "has_parent",
        "created_at",
    ]
    list_filter = ["is_read", "academy"]
    search_fields = [
        "subject",
        "body",
        "sender__email",
        "recipient__email",
    ]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["sender", "recipient", "academy", "parent"]
    list_select_related = ["sender", "recipient", "academy", "parent"]

    @admin.display(description="Is Reply", boolean=True)
    def has_parent(self, obj):
        return obj.parent is not None


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["sender", "academy", "short_message", "created_at"]
    list_filter = ["academy"]
    search_fields = ["message", "sender__email"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["sender", "academy"]
    list_select_related = ["sender", "academy"]

    @admin.display(description="Message")
    def short_message(self, obj):
        if len(obj.message) > 80:
            return obj.message[:80] + "..."
        return obj.message
