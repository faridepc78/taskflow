from typing import cast

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render

from ..selectors.project import (
    get_active_projects_for_user,
    get_dashboard_stats,
)


@login_required
def dashboard(request):
    user = cast(User, request.user)

    projects = list(get_active_projects_for_user(user))

    for project in projects:
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
