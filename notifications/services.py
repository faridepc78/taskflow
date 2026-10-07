from django.contrib.auth.models import User
from django.utils import timezone

from .models import Notification


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
    return Notification.objects.filter(
        user=user,
        is_read=False,
    ).update(
        is_read=True,
        read_at=timezone.now(),
    )
