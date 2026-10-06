from django.contrib.auth.models import User
from django.db.models import Count, Q, QuerySet
from django.shortcuts import get_object_or_404

from ..models import Project


def get_project_for_user(
    *,
    project_id: int,
    user: User,
) -> Project:
    return get_object_or_404(
        Project,
        pk=project_id,
        owner=user,
    )


def get_active_projects_for_user(user: User) -> QuerySet[Project]:
    return (
        Project.objects.filter(
            owner=user,
            is_archived=False,
        )
        .annotate(
            total_tasks=Count("tasks"),
            completed_tasks=Count(
                "tasks",
                filter=Q(tasks__status="done"),
            ),
        )
        .order_by("-created_at")
    )


def get_archived_projects_for_user(user: User) -> QuerySet[Project]:
    return Project.objects.filter(
        owner=user,
        is_archived=True,
    ).order_by("-updated_at")


def get_dashboard_stats(user: User) -> dict:
    projects = Project.objects.filter(owner=user)

    task_stats = projects.aggregate(
        total_projects=Count(
            "id",
            distinct=True,
            filter=Q(is_archived=False),
        ),
        archived_projects=Count(
            "id",
            distinct=True,
            filter=Q(is_archived=True),
        ),
        total_tasks=Count(
            "tasks",
            filter=Q(is_archived=False),
        ),
        completed_tasks=Count(
            "tasks",
            filter=Q(
                is_archived=False,
                tasks__status="done",
            ),
        ),
    )

    total_tasks = task_stats["total_tasks"] or 0
    completed_tasks = task_stats["completed_tasks"] or 0

    completion_rate = round((completed_tasks / total_tasks) * 100) if total_tasks else 0

    return {
        **task_stats,
        "completion_rate": completion_rate,
    }
