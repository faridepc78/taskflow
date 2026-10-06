from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..models import Project, Task, TaskAttachment

DEADLINE_FILTERS = (
    ("overdue", "Overdue"),
    ("today", "Due today"),
    ("upcoming", "Upcoming"),
    ("no_due_date", "No due date"),
)

ALLOWED_TASK_ORDERING = {
    "created_at",
    "-created_at",
    "due_date",
    "-due_date",
    "title",
    "-title",
}


def get_task_for_user(*, task_id: int, user: User) -> Task:
    return get_object_or_404(
        Task,
        pk=task_id,
        project__owner=user,
    )


def get_attachment_for_user(*, attachment_id: int, user: User) -> TaskAttachment:
    return get_object_or_404(
        TaskAttachment,
        pk=attachment_id,
        task__project__owner=user,
    )


def get_filtered_project_tasks(
    project: Project,
    *,
    search: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    deadline: str | None = None,
    ordering: str = "-created_at",
):
    tasks = project.tasks.prefetch_related("categories", "attachments").all()

    if search:
        tasks = tasks.filter(title__icontains=search)

    if status:
        tasks = tasks.filter(status=status)

    if priority:
        tasks = tasks.filter(priority=priority)

    today = timezone.localdate()

    if deadline == "overdue":
        tasks = tasks.filter(due_date__lt=today).exclude(status=Task.Status.DONE)
    elif deadline == "today":
        tasks = tasks.filter(due_date=today).exclude(status=Task.Status.DONE)
    elif deadline == "upcoming":
        tasks = tasks.filter(due_date__gt=today).exclude(status=Task.Status.DONE)
    elif deadline == "no_due_date":
        tasks = tasks.filter(due_date__isnull=True)

    if ordering not in ALLOWED_TASK_ORDERING:
        ordering = "-created_at"

    return tasks.order_by(ordering), ordering
