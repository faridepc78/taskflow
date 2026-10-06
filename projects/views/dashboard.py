from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..selectors import get_active_projects_for_user


@login_required
def dashboard(request):
    projects = get_active_projects_for_user(request.user)

    return render(
        request,
        "projects/dashboard.html",
        {
            "projects": projects,
        },
    )
