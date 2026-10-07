from typing import cast

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import render

from ..selectors.project import (
    get_active_projects_for_user,
    get_dashboard_stats,
)


@login_required
def dashboard(request):
    user = cast(User, request.user)

    projects_queryset = get_active_projects_for_user(user)
    paginator = Paginator(projects_queryset, 12)
    projects = paginator.get_page(request.GET.get("page"))

    for project in projects.object_list:
        project.progress_percentage = (
            round((project.completed_tasks / project.total_tasks) * 100)
            if project.total_tasks
            else 0
        )

    stats = get_dashboard_stats(user)

    return render(
        request,
        "projects/dashboard.html",
        {
            "projects": projects,
            "stats": stats,
        },
    )
