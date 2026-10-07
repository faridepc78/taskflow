from celery import shared_task

from .services import create_deadline_notifications


@shared_task
def create_scheduled_deadline_notifications() -> dict[str, int]:
    return create_deadline_notifications()
