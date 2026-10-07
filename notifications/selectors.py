from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from projects.models import Task

from .cache import UNREAD_COUNT_CACHE_TIMEOUT, get_unread_count_cache_key
from .models import Notification


def get_notifications_for_user(user: User) -> QuerySet[Notification]:
    return Notification.objects.filter(user=user).order_by("-created_at", "-id")


def get_unread_notification_count(user: User) -> int:
    cache_key = get_unread_count_cache_key(user.id)
    cached_count = cache.get(cache_key)

    if cached_count is not None:
        return cached_count

    unread_count = Notification.objects.filter(
        user=user,
        is_read=False,
    ).count()

    cache.set(
        cache_key,
        unread_count,
        timeout=UNREAD_COUNT_CACHE_TIMEOUT,
    )

    return unread_count


def get_notification_for_user(*, notification_id: int, user: User) -> Notification:
    return get_object_or_404(
        Notification,
        pk=notification_id,
        user=user,
    )


def get_pending_tasks_with_deadline() -> QuerySet[Task]:
    return (
        Task.objects.select_related("project", "project__owner")
        .filter(
            project__is_archived=False,
            due_date__isnull=False,
        )
        .exclude(status=Task.Status.DONE)
        .order_by("due_date", "id")
    )
