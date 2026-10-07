from datetime import date, timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .cache import invalidate_unread_count_cache
from .models import Notification
from .selectors import get_pending_tasks_with_deadline


def create_notification(
    *,
    user: User,
    title: str,
    message: str,
    kind: str = Notification.Kind.INFO,
    url: str = "",
    deduplication_key: str | None = None,
) -> tuple[Notification, bool]:
    if deduplication_key:
        return Notification.objects.get_or_create(
            user=user,
            deduplication_key=deduplication_key,
            defaults={
                "kind": kind,
                "title": title,
                "message": message,
                "url": url,
            },
        )

    return (
        Notification.objects.create(
            user=user,
            kind=kind,
            title=title,
            message=message,
            url=url,
        ),
        True,
    )


def mark_notification_as_read(notification: Notification) -> None:
    notification.mark_as_read()


def mark_all_notifications_as_read(user: User) -> int:
    updated_count = Notification.objects.filter(
        user=user,
        is_read=False,
    ).update(
        is_read=True,
        read_at=timezone.now(),
    )

    invalidate_unread_count_cache(user.id)

    return updated_count


def create_deadline_notifications(
    *,
    current_date: date | None = None,
) -> dict[str, int]:
    today = current_date or timezone.localdate()
    tomorrow = today + timedelta(days=1)

    counters = {
        "reminder": 0,
        "deadline": 0,
        "overdue": 0,
    }

    for task in get_pending_tasks_with_deadline().iterator(chunk_size=200):
        if task.due_date is None:
            continue

        project_url = reverse("projects:detail", kwargs={"pk": task.project_id})
        user = task.project.owner

        if task.due_date == tomorrow:
            _, created = create_notification(
                user=user,
                kind=Notification.Kind.REMINDER,
                title="Task due tomorrow",
                message=f'"{task.title}" is due tomorrow.',
                url=project_url,
                deduplication_key=(
                    f"task:{task.pk}:reminder:{task.due_date.isoformat()}"
                ),
            )
            counters["reminder"] += int(created)
            continue

        if task.due_date == today:
            _, created = create_notification(
                user=user,
                kind=Notification.Kind.DEADLINE,
                title="Task due today",
                message=f'"{task.title}" is due today.',
                url=project_url,
                deduplication_key=(
                    f"task:{task.pk}:deadline:{task.due_date.isoformat()}"
                ),
            )
            counters["deadline"] += int(created)
            continue

        if task.due_date < today:
            _, created = create_notification(
                user=user,
                kind=Notification.Kind.OVERDUE,
                title="Task overdue",
                message=(
                    f'"{task.title}" was due on '
                    f"{task.due_date.isoformat()} and is still incomplete."
                ),
                url=project_url,
                deduplication_key=(f"task:{task.pk}:overdue:{today.isoformat()}"),
            )
            counters["overdue"] += int(created)

    return counters
