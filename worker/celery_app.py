from celery import Celery
from celery.schedules import crontab

from shared.config import REDIS_URL

app = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Bucharest",
    enable_utc=True,
    beat_schedule={
        "daily-scrape": {
            "task": "tasks.scrape_all_sources",
            "schedule": crontab(hour=6, minute=0),
        },
    },
)

import tasks  # noqa: F401, E402
