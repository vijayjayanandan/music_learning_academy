from django.urls import path
from . import views

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notification-list"),
    path("<int:pk>/read/", views.MarkReadView.as_view(), name="notification-mark-read"),
    path("mark-all-read/", views.MarkAllReadView.as_view(), name="notification-mark-all-read"),
    path("partials/badge/", views.NotificationBadgePartialView.as_view(), name="notification-badge-partial"),
]
