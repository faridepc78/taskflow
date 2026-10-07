from typing import cast

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..forms import TaskForm
from ..models import Activity, Task
from ..selectors.project import get_project_for_user
from ..selectors.task import get_task_for_user
from ..services import change_task_status, log_activity


@login_required
def task_create(request, project_pk):
    user = cast(User, request.user)

    project = get_project_for_user(
        project_id=project_pk,
        user=user,
    )

    if request.method == "POST":
        form = TaskForm(request.POST, user=user)

        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            form.save_m2m()
            log_activity(
                project=project,
                actor=user,
                action=Activity.Action.TASK_CREATED,
                description=f'Created task "{task.title}".',
                task=task,
            )

            return redirect(
                "projects:detail",
                pk=project.pk,
            )
    else:
        form = TaskForm(user=user)

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
    user = cast(User, request.user)

    task = get_task_for_user(
        task_id=pk,
        user=user,
    )

    if request.method == "POST":
        form = TaskForm(
            request.POST,
            instance=task,
            user=user,
        )

        if form.is_valid():
            task = form.save()
            log_activity(
                project=task.project,
                actor=user,
                action=Activity.Action.TASK_UPDATED,
                description=f'Updated task "{task.title}".',
                task=task,
            )

            return redirect(
                "projects:detail",
                pk=task.project.pk,
            )
    else:
        form = TaskForm(instance=task, user=user)

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
    user = cast(User, request.user)

    task = get_task_for_user(
        task_id=pk,
        user=user,
    )

    project_pk = task.project.pk

    if request.method == "POST":
        log_activity(
            project=task.project,
            actor=user,
            action=Activity.Action.TASK_DELETED,
            description=f'Deleted task "{task.title}".',
            task=task,
        )
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


@require_POST
@login_required
def task_change_status(request, pk):
    user = cast(User, request.user)

    task = get_task_for_user(
        task_id=pk,
        user=user,
    )

    status = request.POST.get("status", "")

    if status not in Task.Status.values:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid task status.",
            },
            status=400,
        )

    old_status = task.get_status_display()
    change_task_status(task=task, status=status)
    if old_status != task.get_status_display():
        log_activity(
            project=task.project,
            actor=user,
            action=Activity.Action.TASK_STATUS_CHANGED,
            description=f'Changed task "{task.title}" status from {old_status} to {task.get_status_display()}.',
            task=task,
        )

    total_tasks = task.project.tasks.count()
    completed_tasks = task.project.tasks.filter(status=Task.Status.DONE).count()
    progress_percentage = (
        round((completed_tasks / total_tasks) * 100) if total_tasks else 0
    )

    return JsonResponse(
        {
            "success": True,
            "status": task.status,
            "status_label": task.get_status_display(),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress_percentage": progress_percentage,
        }
    )
