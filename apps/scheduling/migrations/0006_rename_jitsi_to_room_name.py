"""Rename jitsi_room_name to room_name, replace Jitsi with LiveKit."""

from django.db import migrations, models


def migrate_jitsi_to_livekit(apps, schema_editor):
    """Update all existing sessions using jitsi platform to livekit."""
    LiveSession = apps.get_model("scheduling", "LiveSession")
    LiveSession.objects.filter(video_platform="jitsi").update(video_platform="livekit")


def migrate_livekit_to_jitsi(apps, schema_editor):
    """Reverse: update livekit back to jitsi."""
    LiveSession = apps.get_model("scheduling", "LiveSession")
    LiveSession.objects.filter(video_platform="livekit").update(video_platform="jitsi")


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0005_livesession_external_meeting_url_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="livesession",
            old_name="jitsi_room_name",
            new_name="room_name",
        ),
        migrations.AlterField(
            model_name="livesession",
            name="video_platform",
            field=models.CharField(
                choices=[
                    ("livekit", "LiveKit"),
                    ("zoom", "Zoom"),
                    ("google_meet", "Google Meet"),
                    ("custom", "Custom URL"),
                ],
                default="livekit",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="livesession",
            name="external_meeting_url",
            field=models.URLField(
                blank=True,
                help_text="External meeting URL if not using LiveKit",
            ),
        ),
        migrations.RunPython(
            migrate_jitsi_to_livekit,
            migrate_livekit_to_jitsi,
        ),
    ]
