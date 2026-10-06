from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectForm, TaskForm
from .models import Project, Task


@login_required
def dashboard(request):
    projects = Project.objects.filter(
        owner=request.user,
        is_archived=False,
    ).order_by("-created_at")

    return render(
        request,
        "projects/dashboard.html",
        {
            "projects": projects,
        },
    )


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
    project = get_object_or_404(
        Project,
        pk=pk,
        owner=request.user,
    )

    tasks = project.tasks.all()

    search = request.GET.get("search")
    status = request.GET.get("status")
    priority = request.GET.get("priority")
    ordering = request.GET.get("ordering", "-created_at")

    if search:
        tasks = tasks.filter(title__icontains=search)

    if status:
        tasks = tasks.filter(status=status)

    if priority:
        tasks = tasks.filter(priority=priority)

    allowed_ordering = {
        "created_at",
        "-created_at",
        "due_date",
        "-due_date",
        "title",
        "-title",
    }

    if ordering not in allowed_ordering:
        ordering = "-created_at"

    tasks = tasks.order_by(ordering)

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
    project = get_object_or_404(
        Project,
        pk=pk,
        owner=request.user,
    )

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
    project = get_object_or_404(
        Project,
        pk=pk,
        owner=request.user,
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
def task_create(request, project_pk):
    project = get_object_or_404(
        Project,
        pk=project_pk,
        owner=request.user,
    )

    if request.method == "POST":
        form = TaskForm(request.POST)

        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()

            form.save_m2m()

            return redirect(
                "projects:detail",
                pk=project.pk,
            )
    else:
        form = TaskForm()

    return render(
        request,
        "projects/task_form.html",
        {
            "form": form,
            "project": project,
            "title": "Create task",
        },
    )


@login_required
def task_update(request, pk):
    task = get_object_or_404(
        Task,
        pk=pk,
        project__owner=request.user,
    )

    if request.method == "POST":
        form = TaskForm(
            request.POST,
            instance=task,
        )

        if form.is_valid():
            form.save()

            return redirect(
                "projects:detail",
                pk=task.project.pk,
            )

    else:
        form = TaskForm(instance=task)

    return render(
        request,
        "projects/task_form.html",
        {
            "form": form,
            "project": task.project,
            "task": task,
            "title": "Edit task",
        },
    )


@login_required
def task_delete(request, pk):
    task = get_object_or_404(
        Task,
        pk=pk,
        project__owner=request.user,
    )

    project_pk = task.project.pk

    if request.method == "POST":
        task.delete()

        return redirect(
            "projects:detail",
            pk=project_pk,
        )

    return render(
        request,
        "projects/task_confirm_delete.html",
        {
            "task": task,
        },
    )
