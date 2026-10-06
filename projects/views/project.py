from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..forms import ProjectForm
from ..models import Activity, Task
from ..selectors.project import (
    get_archived_projects_for_user,
    get_project_activities,
    get_project_for_user,
)
from ..selectors.task import DEADLINE_FILTERS, get_filtered_project_tasks
from ..services import archive_project, log_activity, restore_project


@login_required
def project_create(request):
    user = cast(User, request.user)

    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            project = form.save(commit=False)
            project.owner = user
            project.save()
            log_activity(
                project=project,
                actor=user,
                action=Activity.Action.PROJECT_CREATED,
                description=f'Created project "{project.name}".',
            )

            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm()

    return render(
        request,
        "projects/project_form.html",
        {
            "form": form,
            "title": "Create project",
        },
    )


@login_required
def project_detail(request, pk):
    user = cast(User, request.user)

    project = get_project_for_user(
        project_id=pk,
        user=user,
    )

    search = request.GET.get("search")
    status = request.GET.get("status")
    priority = request.GET.get("priority")
    deadline = request.GET.get("deadline")
    ordering = request.GET.get("ordering", "-created_at")

    tasks, ordering = get_filtered_project_tasks(
        project,
        search=search,
        status=status,
        priority=priority,
        deadline=deadline,
        ordering=ordering,
    )

    activities = get_project_activities(project)

    total_tasks = project.tasks.count()
    completed_tasks = project.tasks.filter(status=Task.Status.DONE).count()

    progress_percentage = (
        round((completed_tasks / total_tasks) * 100) if total_tasks else 0
    )

    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "tasks": tasks,
            "statuses": Task.Status.choices,
            "priorities": Task.Priority.choices,
            "deadline_filters": DEADLINE_FILTERS,
            "current_search": search or "",
            "current_status": status or "",
            "current_priority": priority or "",
            "current_deadline": deadline or "",
            "current_ordering": ordering,
            "progress_percentage": progress_percentage,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "activities": activities,
        },
    )


@login_required
def project_update(request, pk):
    user = cast(User, request.user)

    project = get_project_for_user(
        project_id=pk,
        user=user,
    )

    if request.method == "POST":
        form = ProjectForm(
            request.POST,
            instance=project,
        )

        if form.is_valid():
            form.save()
            log_activity(
                project=project,
                actor=user,
                action=Activity.Action.PROJECT_UPDATED,
                description=f'Updated project "{project.name}".',
            )

            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    return render(
        request,
        "projects/project_form.html",
        {
            "form": form,
            "title": "Edit project",
            "project": project,
        },
    )


@login_required
def project_delete(request, pk):
    user = cast(User, request.user)

    project = get_project_for_user(
        project_id=pk,
        user=user,
    )

    if request.method == "POST":
        project.delete()
        return redirect("projects:dashboard")

    return render(
        request,
        "projects/project_confirm_delete.html",
        {
            "project": project,
        },
    )


@login_required
def archived_projects(request):
    user = cast(User, request.user)

    projects = get_archived_projects_for_user(user)

    return render(
        request,
        "projects/archived_projects.html",
        {
            "projects": projects,
        },
    )


@require_POST
@login_required
def project_archive(request, pk):
    user = cast(User, request.user)

    project = get_project_for_user(
        project_id=pk,
        user=user,
    )

    archive_project(project)
    log_activity(
        project=project,
        actor=user,
        action=Activity.Action.PROJECT_ARCHIVED,
        description=f'Archived project "{project.name}".',
    )

    messages.success(
        request,
        "Project archived successfully.",
    )

    return redirect("projects:dashboard")


@require_POST
@login_required
def project_restore(request, pk):
    user = cast(User, request.user)

    project = get_project_for_user(
        project_id=pk,
        user=user,
    )

    restore_project(project)
    log_activity(
        project=project,
        actor=user,
        action=Activity.Action.PROJECT_RESTORED,
        description=f'Restored project "{project.name}".',
    )

    messages.success(
        request,
        "Project restored successfully.",
    )

    return redirect("projects:archived")
