from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..forms import TaskAttachmentForm
from ..guards import require_active_project
from ..models import Activity
from ..selectors.task import get_attachment_for_user, get_task_for_user
from ..services import log_activity


@transaction.atomic
@login_required
def attachment_upload(request, task_pk):
    user = cast(User, request.user)

    task = get_task_for_user(
        task_id=task_pk,
        user=user,
    )

    require_active_project(task.project)

    if request.method == "POST":
        form = TaskAttachmentForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.task = task
            attachment.save()
            log_activity(
                project=task.project,
                actor=user,
                action=Activity.Action.ATTACHMENT_UPLOADED,
                description=f'Uploaded attachment "{attachment.filename}" to task "{task.title}".',
                task=task,
            )

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


@transaction.atomic
@require_POST
@login_required
def attachment_delete(request, pk):
    user = cast(User, request.user)

    attachment = get_attachment_for_user(
        attachment_id=pk,
        user=user,
    )

    require_active_project(attachment.task.project)

    project_pk = attachment.task.project.pk
    task = attachment.task
    filename = attachment.filename
    log_activity(
        project=task.project,
        actor=user,
        action=Activity.Action.ATTACHMENT_DELETED,
        description=f'Deleted attachment "{filename}" from task "{task.title}".',
        task=task,
    )
    attachment.delete()

    messages.success(
        request,
        "Attachment deleted successfully.",
    )

    return redirect(
        "projects:detail",
        pk=project_pk,
    )


@login_required
def attachment_download(request, pk):
    attachment = get_attachment_for_user(attachment_id=pk, user=request.user)
    try:
        stream = attachment.file.open("rb")
    except (FileNotFoundError, OSError) as exc:
        raise Http404("Attachment not found.") from exc
    response = FileResponse(stream, as_attachment=True, filename=attachment.filename, content_type="application/octet-stream")
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response
