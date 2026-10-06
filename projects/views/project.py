from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..forms import ProjectForm
from ..models import Task
from ..selectors import get_filtered_project_tasks, get_project_for_user


@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()

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
    project = get_project_for_user(request.user, pk)

    search = request.GET.get("search")
    status = request.GET.get("status")
    priority = request.GET.get("priority")
    ordering = request.GET.get("ordering", "-created_at")

    tasks, ordering = get_filtered_project_tasks(
        project,
        search=search,
        status=status,
        priority=priority,
        ordering=ordering,
    )

    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "tasks": tasks,
            "statuses": Task.Status.choices,
            "priorities": Task.Priority.choices,
            "current_search": search or "",
            "current_status": status or "",
            "current_priority": priority or "",
            "current_ordering": ordering,
        },
    )


@login_required
def project_update(request, pk):
    project = get_project_for_user(request.user, pk)

    if request.method == "POST":
        form = ProjectForm(
            request.POST,
            instance=project,
        )

        if form.is_valid():
            form.save()

            return redirect(
                "projects:detail",
                pk=project.pk,
            )

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
    project = get_project_for_user(request.user, pk)

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
