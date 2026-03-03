from django.urls import path
from . import views

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notification-list"),
    path("<int:pk>/read/", views.MarkReadView.as_view(), name="notification-mark-read"),
    path("mark-all-read/", views.MarkAllReadView.as_view(), name="notification-mark-all-read"),
    path("partials/badge/", views.NotificationBadgePartialView.as_view(), name="notification-badge-partial"),
    # Messaging
    path("messages/", views.InboxView.as_view(), name="message-inbox"),
    path("messages/sent/", views.SentView.as_view(), name="message-sent"),
    path("messages/compose/", views.ComposeMessageView.as_view(), name="message-compose"),
    path("messages/<int:pk>/", views.MessageThreadView.as_view(), name="message-thread"),
    path("messages/unread-count/", views.UnreadMessageCountView.as_view(), name="message-unread-count"),
    path("chat/<slug:slug>/", views.CourseChatView.as_view(), name="course-chat"),
]
