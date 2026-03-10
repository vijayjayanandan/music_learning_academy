from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from apps.academies.mixins import TenantMixin
from .models import (
    EarTrainingExercise,
    EarTrainingScore,
    RecitalEvent,
    PracticeAnalysis,
    RecordingArchive,
)


class MetronomeView(LoginRequiredMixin, View):
    """FEAT-033: Built-in metronome (Web Audio API)."""

    def get(self, request):
        return render(request, "music_tools/metronome.html")


class TunerView(LoginRequiredMixin, View):
    """FEAT-034: Built-in tuner (mic-based pitch detection)."""

    def get(self, request):
        return render(request, "music_tools/tuner.html")


class NotationView(LoginRequiredMixin, View):
    """FEAT-035: Music notation renderer."""

    def get(self, request):
        return render(request, "music_tools/notation.html")


class EarTrainingListView(TenantMixin, ListView):
    """FEAT-036: Ear training exercises list."""

    model = EarTrainingExercise
    template_name = "music_tools/ear_training_list.html"
    context_object_name = "exercises"

    def get_queryset(self):
        return EarTrainingExercise.objects.filter(
            academy=self.get_academy(),
            is_active=True,
        )


class EarTrainingPlayView(TenantMixin, View):
    """Play an ear training exercise."""

    def get(self, request, pk):
        exercise = get_object_or_404(
            EarTrainingExercise,
            pk=pk,
            academy=self.get_academy(),
        )
        return render(
            request,
            "music_tools/ear_training_play.html",
            {
                "exercise": exercise,
            },
        )

    def post(self, request, pk):
        exercise = get_object_or_404(
            EarTrainingExercise,
            pk=pk,
            academy=self.get_academy(),
        )
        score = int(request.POST.get("score", 0))
        total = int(request.POST.get("total_questions", 0))
        time_taken = int(request.POST.get("time_taken", 0))
        EarTrainingScore.objects.create(
            student=request.user,
            exercise=exercise,
            academy=self.get_academy(),
            score=score,
            total_questions=total,
            time_taken_seconds=time_taken,
        )
        return redirect("ear-training-list")


class RecitalListView(TenantMixin, ListView):
    """FEAT-037: Virtual recital events."""

    model = RecitalEvent
    template_name = "music_tools/recital_list.html"
    context_object_name = "recitals"

    def get_queryset(self):
        return RecitalEvent.objects.filter(academy=self.get_academy())


class RecitalDetailView(TenantMixin, View):
    """View recital details and watch."""

    def get(self, request, pk):
        recital = get_object_or_404(
            RecitalEvent,
            pk=pk,
            academy=self.get_academy(),
        )
        performers = recital.performers.select_related("student").all()
        return render(
            request,
            "music_tools/recital_detail.html",
            {
                "recital": recital,
                "performers": performers,
            },
        )


class RecitalCreateView(TenantMixin, View):
    """Create a new recital event."""

    def dispatch(self, request, *args, **kwargs):
        # Security: only instructors and owners can create recitals
        if hasattr(request, "academy") and request.academy:
            role = request.user.get_role_in(request.academy)
            if role not in ("owner", "instructor"):
                from django.http import HttpResponseForbidden

                return HttpResponseForbidden(
                    "Only instructors and owners can create recitals."
                )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, "music_tools/recital_create.html")

    def post(self, request):
        from apps.scheduling.jitsi import generate_room_name

        recital = RecitalEvent.objects.create(
            academy=self.get_academy(),
            title=request.POST.get("title", ""),
            description=request.POST.get("description", ""),
            scheduled_start=request.POST.get("scheduled_start"),
            scheduled_end=request.POST.get("scheduled_end"),
            room_name=generate_room_name(self.get_academy().slug, "recital"),
        )
        return redirect("recital-detail", pk=recital.pk)


class PracticeAnalysisView(TenantMixin, View):
    """FEAT-038: AI practice feedback."""

    ALLOWED_RECORDING_EXTENSIONS = {
        ".mp3",
        ".wav",
        ".ogg",
        ".flac",
        ".m4a",
        ".mp4",
        ".webm",
        ".mov",
    }
    MAX_RECORDING_SIZE = 100 * 1024 * 1024  # 100MB

    def get(self, request):
        analyses = PracticeAnalysis.objects.filter(
            student=request.user,
            academy=self.get_academy(),
        )[:10]
        return render(
            request,
            "music_tools/practice_analysis.html",
            {
                "analyses": analyses,
            },
        )

    def post(self, request):
        import os

        analysis = PracticeAnalysis.objects.create(
            student=request.user,
            academy=self.get_academy(),
        )
        if request.FILES.get("recording"):
            recording = request.FILES["recording"]
            ext = os.path.splitext(recording.name)[1].lower()
            # Security: validate file type and size
            if (
                ext in self.ALLOWED_RECORDING_EXTENSIONS
                and recording.size <= self.MAX_RECORDING_SIZE
            ):
                analysis.recording = recording
                analysis.save()
        # In production, would send to analysis pipeline here
        # For PoC, generate mock analysis
        analysis.analysis_result = {
            "pitch_accuracy": 85,
            "rhythm_accuracy": 90,
            "tempo_stability": 78,
            "dynamics": 82,
            "overall": 84,
        }
        analysis.feedback = "Good overall performance! Focus on maintaining consistent tempo in the middle section."
        analysis.analyzed_at = timezone.now()
        analysis.save()
        return redirect("practice-analysis")


class RecordingArchiveView(TenantMixin, ListView):
    """FEAT-039: Recording archive per student."""

    model = RecordingArchive
    template_name = "music_tools/recording_archive.html"
    context_object_name = "recordings"
    paginate_by = 20

    def get_queryset(self):
        qs = RecordingArchive.objects.filter(
            student=self.request.user,
            academy=self.get_academy(),
        )
        instrument = self.request.GET.get("instrument")
        if instrument:
            qs = qs.filter(instrument=instrument)
        return qs


class RecordingUploadView(TenantMixin, View):
    """Upload a new recording to the archive."""

    ALLOWED_RECORDING_EXTENSIONS = {
        ".mp3",
        ".wav",
        ".ogg",
        ".flac",
        ".m4a",
        ".mp4",
        ".webm",
        ".mov",
    }
    MAX_RECORDING_SIZE = 100 * 1024 * 1024  # 100MB

    def post(self, request):
        import os

        if request.FILES.get("recording"):
            recording = request.FILES["recording"]
            ext = os.path.splitext(recording.name)[1].lower()
            # Security: validate file type and size
            if ext not in self.ALLOWED_RECORDING_EXTENSIONS:
                from django.contrib import messages

                messages.error(
                    request, f"File type '{ext}' is not allowed for recordings."
                )
                return redirect("recording-archive")
            if recording.size > self.MAX_RECORDING_SIZE:
                from django.contrib import messages

                messages.error(request, "Recording exceeds the 100MB size limit.")
                return redirect("recording-archive")
            RecordingArchive.objects.create(
                student=request.user,
                academy=self.get_academy(),
                title=request.POST.get("title", "Untitled"),
                recording=recording,
                instrument=request.POST.get("instrument", ""),
                notes=request.POST.get("notes", ""),
            )
        return redirect("recording-archive")


class CalendarSyncView(TenantMixin, View):
    """FEAT-040: Calendar sync (iCal feed)."""

    def get(self, request):
        import secrets

        user = request.user
        if not user.ical_feed_token:
            user.ical_feed_token = secrets.token_urlsafe(32)
            user.save(update_fields=["ical_feed_token"])
        feed_url = request.build_absolute_uri(f"/schedule/ical/{user.ical_feed_token}/")
        return render(
            request,
            "music_tools/calendar_sync.html",
            {
                "feed_url": feed_url,
            },
        )


class ICalFeedView(View):
    """Generate iCal feed for a user's sessions."""

    def get(self, request, token):
        from django.http import HttpResponse
        from apps.accounts.models import User
        from apps.scheduling.models import LiveSession, SessionAttendance

        user = get_object_or_404(User, ical_feed_token=token)
        # Get all sessions user is involved in
        instructor_sessions = LiveSession.objects.filter(instructor=user)
        attended_ids = SessionAttendance.objects.filter(student=user).values_list(
            "session_id", flat=True
        )
        student_sessions = LiveSession.objects.filter(pk__in=attended_ids)
        all_sessions = instructor_sessions | student_sessions

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Music Learning Academy//EN",
            "CALSCALE:GREGORIAN",
        ]
        for session in all_sessions.distinct():
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:session-{session.pk}@musicacademy",
                    f"DTSTART:{session.scheduled_start.strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTEND:{session.scheduled_end.strftime('%Y%m%dT%H%M%SZ')}",
                    f"SUMMARY:{session.title}",
                    f"DESCRIPTION:{session.description}",
                    "END:VEVENT",
                ]
            )
        lines.append("END:VCALENDAR")
        content = "\r\n".join(lines)
        return HttpResponse(content, content_type="text/calendar")
