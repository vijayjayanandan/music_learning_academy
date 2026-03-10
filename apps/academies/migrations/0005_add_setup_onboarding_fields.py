from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academies", "0004_r2_storage_backends"),
    ]

    operations = [
        migrations.AddField(
            model_name="academy",
            name="setup_status",
            field=models.CharField(
                choices=[
                    ("new", "New"),
                    ("basics_done", "Basics Done"),
                    ("branding_done", "Branding Done"),
                    ("team_invited", "Team Invited"),
                    ("catalog_ready", "Catalog Ready"),
                    ("live", "Live"),
                ],
                default="new",
                help_text="Current setup wizard progress",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="academy",
            name="currency",
            field=models.CharField(
                default="USD",
                help_text="ISO 4217 currency code (e.g., USD, EUR, GBP, INR)",
                max_length=3,
            ),
        ),
        migrations.AddField(
            model_name="academy",
            name="minor_mode_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Enable COPPA/minor safety features for this academy",
            ),
        ),
    ]
