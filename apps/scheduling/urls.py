from django.urls import path
from . import views

urlpatterns = [
    path("", views.ScheduleListView.as_view(), name="schedule-list"),
    path("session/create/", views.SessionCreateView.as_view(), name="session-create"),
    path("session/<int:pk>/", views.SessionDetailView.as_view(), name="session-detail"),
    path("session/<int:pk>/edit/", views.SessionEditView.as_view(), name="session-edit"),
    path("session/<int:pk>/cancel/", views.CancelSessionView.as_view(), name="session-cancel"),
    path("session/<int:pk>/register/", views.RegisterForSessionView.as_view(), name="session-register"),
    path("session/<int:pk>/join/", views.JoinSessionView.as_view(), name="session-join"),
    path("session/<int:pk>/mark-joined/", views.MarkJoinedView.as_view(), name="session-mark-joined"),
    path("session/<int:pk>/mark-left/", views.MarkLeftView.as_view(), name="session-mark-left"),
    path("partials/upcoming/", views.UpcomingSessionsPartialView.as_view(), name="upcoming-sessions-partial"),
    path("api/events/", views.SessionEventsAPIView.as_view(), name="session-events-api"),
    path("availability/", views.AvailabilityManageView.as_view(), name="availability-manage"),
    path("availability/<int:pk>/delete/", views.DeleteAvailabilityView.as_view(), name="availability-delete"),
    path("book/", views.BookSessionView.as_view(), name="book-session"),
]
