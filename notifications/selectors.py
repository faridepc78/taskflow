from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from projects.models import Task

from .models import Notification


def get_notifications_for_user(user: User) -> QuerySet[Notification]:
    return Notification.objects.filter(user=user).order_by("-created_at", "-id")


def get_unread_notification_count(user: User) -> int:
    return Notification.objects.filter(
        user=user,
        is_read=False,
    ).count()


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
