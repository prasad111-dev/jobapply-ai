from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "jobapply",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=250,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    beat_schedule={
        "sync-jobs-hourly": {
            "task": "app.workers.tasks.sync_all_platforms",
            "schedule": 3600.0,
        },
        "check-job-alerts-daily": {
            "task": "app.workers.tasks.check_job_alerts",
            "schedule": 86400.0,
        },
    },
)
