"""Rename jitsi_room_name to room_name on RecitalEvent."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("music_tools", "0002_r2_storage_backends"),
    ]

    operations = [
        migrations.RenameField(
            model_name="recitalevent",
            old_name="jitsi_room_name",
            new_name="room_name",
        ),
    ]
