import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("music_academy")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    "send-session-reminders-every-5-min": {
        "task": "apps.scheduling.tasks.send_session_reminders",
        "schedule": crontab(minute="*/5"),
    },
    "expire-trials-daily": {
        "task": "apps.payments.tasks.expire_trials",
        "schedule": crontab(hour=0, minute=30),
    },
    "generate-recurring-sessions-daily": {
        "task": "apps.scheduling.tasks.generate_recurring_sessions",
        "schedule": crontab(hour=1, minute=0),
    },
}
