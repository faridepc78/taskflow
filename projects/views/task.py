from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..forms import TaskForm
from ..selectors import get_project_for_user, get_task_for_user


@login_required
def task_create(request, project_pk):
    project = get_project_for_user(request.user, project_pk)

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
    task = get_task_for_user(request.user, pk)

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
    task = get_task_for_user(request.user, pk)

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
