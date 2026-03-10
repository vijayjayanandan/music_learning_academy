# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0012_add_membership_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="membership",
            name="learning_goal",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="membership",
            name="onboarding_skipped",
            field=models.BooleanField(default=False),
        ),
    ]
