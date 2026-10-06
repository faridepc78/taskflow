from django.shortcuts import get_object_or_404

from ..models import Task

ALLOWED_TASK_ORDERING = {
    "created_at",
    "-created_at",
    "due_date",
    "-due_date",
    "title",
    "-title",
}


def get_task_for_user(user, pk):
    return get_object_or_404(
        Task,
        pk=pk,
        project__owner=user,
    )


def get_filtered_project_tasks(
    project,
    *,
    search=None,
    status=None,
    priority=None,
    ordering="-created_at",
):
    tasks = project.tasks.all()

    if search:
        tasks = tasks.filter(title__icontains=search)

    if status:
        tasks = tasks.filter(status=status)

    if priority:
        tasks = tasks.filter(priority=priority)

    if ordering not in ALLOWED_TASK_ORDERING:
        ordering = "-created_at"

    return tasks.order_by(ordering), ordering
