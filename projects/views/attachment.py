from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..forms import TaskAttachmentForm
from ..selectors.task import get_attachment_for_user, get_task_for_user


@login_required
def attachment_upload(request, task_pk):
    user = cast(User, request.user)

    task = get_task_for_user(
        task_id=task_pk,
        user=user,
    )

    if request.method == "POST":
        form = TaskAttachmentForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.task = task
            attachment.save()

            messages.success(
                request,
                "Attachment uploaded successfully.",
            )

            return redirect(
                "projects:detail",
                pk=task.project.pk,
            )
    else:
        form = TaskAttachmentForm()

    return render(
        request,
        "projects/attachment_form.html",
        {
            "form": form,
            "task": task,
        },
    )


@require_POST
@login_required
def attachment_delete(request, pk):
    user = cast(User, request.user)

    attachment = get_attachment_for_user(
        attachment_id=pk,
        user=user,
    )

    project_pk = attachment.task.project.pk
    attachment.delete()

    messages.success(
        request,
        "Attachment deleted successfully.",
    )

    return redirect(
        "projects:detail",
        pk=project_pk,
    )
