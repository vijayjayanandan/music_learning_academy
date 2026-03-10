from django.urls import path
from . import views
from apps.music_tools.views import ICalFeedView as _ical_feed_view_cls

_ical_feed_view = _ical_feed_view_cls.as_view()

urlpatterns = [
    path("", views.ScheduleListView.as_view(), name="schedule-list"),
    path("session/create/", views.SessionCreateView.as_view(), name="session-create"),
    path("session/<int:pk>/", views.SessionDetailView.as_view(), name="session-detail"),
    path("session/<int:pk>/edit/", views.SessionEditView.as_view(), name="session-edit"),
    path("session/<int:pk>/cancel/", views.CancelSessionView.as_view(), name="session-cancel"),
    path("session/<int:pk>/reschedule/", views.RescheduleSessionView.as_view(), name="session-reschedule"),
    path("session/<int:pk>/register/", views.RegisterForSessionView.as_view(), name="session-register"),
    path("session/<int:pk>/join/", views.JoinSessionView.as_view(), name="session-join"),
    path("session/<int:pk>/mark-joined/", views.MarkJoinedView.as_view(), name="session-mark-joined"),
    path("session/<int:pk>/mark-left/", views.MarkLeftView.as_view(), name="session-mark-left"),
    path("session/<int:pk>/start-recording/", views.StartRecordingView.as_view(), name="session-start-recording"),
    path("session/<int:pk>/stop-recording/", views.StopRecordingView.as_view(), name="session-stop-recording"),
    path("partials/upcoming/", views.UpcomingSessionsPartialView.as_view(), name="upcoming-sessions-partial"),
    path("api/events/", views.SessionEventsAPIView.as_view(), name="session-events-api"),
    path("availability/", views.AvailabilityManageView.as_view(), name="availability-manage"),
    path("availability/<int:pk>/delete/", views.DeleteAvailabilityView.as_view(), name="availability-delete"),
    path("book/slots/", views.BookSessionSlotsView.as_view(), name="book-session-slots"),
    path("book/confirm/", views.BookSessionConfirmView.as_view(), name="book-session-confirm"),
    path("book/", views.BookSessionView.as_view(), name="book-session"),
    path("ical/<str:token>/", _ical_feed_view, name="ical-feed"),
]
