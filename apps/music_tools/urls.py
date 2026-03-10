from django.urls import path
from . import views

urlpatterns = [
    # Tools
    path("metronome/", views.MetronomeView.as_view(), name="metronome"),
    path("tuner/", views.TunerView.as_view(), name="tuner"),
    path("notation/", views.NotationView.as_view(), name="notation-renderer"),
    # Ear training
    path(
        "ear-training/", views.EarTrainingListView.as_view(), name="ear-training-list"
    ),
    path(
        "ear-training/<int:pk>/",
        views.EarTrainingPlayView.as_view(),
        name="ear-training-play",
    ),
    # Recitals
    path("recitals/", views.RecitalListView.as_view(), name="recital-list"),
    path("recitals/create/", views.RecitalCreateView.as_view(), name="recital-create"),
    path(
        "recitals/<int:pk>/", views.RecitalDetailView.as_view(), name="recital-detail"
    ),
    # AI Analysis
    path("analysis/", views.PracticeAnalysisView.as_view(), name="practice-analysis"),
    # Recording Archive
    path("recordings/", views.RecordingArchiveView.as_view(), name="recording-archive"),
    path(
        "recordings/upload/",
        views.RecordingUploadView.as_view(),
        name="recording-upload",
    ),
    # Calendar Sync
    path("calendar-sync/", views.CalendarSyncView.as_view(), name="calendar-sync"),
]
