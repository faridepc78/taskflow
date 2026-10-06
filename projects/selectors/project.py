from django.shortcuts import get_object_or_404

from ..models import Project


def get_active_projects_for_user(user):
    return Project.objects.filter(
        owner=user,
        is_archived=False,
    ).order_by("-created_at")


def get_project_for_user(user, pk):
    return get_object_or_404(
        Project,
        pk=pk,
        owner=user,
    )
