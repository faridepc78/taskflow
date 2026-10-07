from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .selectors import (
    get_notification_for_user,
    get_notifications_for_user,
)
from .services import (
    mark_all_notifications_as_read,
    mark_notification_as_read,
)


@login_required
def notification_list(request):
    user = cast(User, request.user)

    return render(
        request,
        "notifications/notification_list.html",
        {
            "notifications": get_notifications_for_user(user),
        },
    )


@require_POST
@login_required
def notification_mark_read(request, pk):
    user = cast(User, request.user)

    notification = get_notification_for_user(
        notification_id=pk,
        user=user,
    )
    mark_notification_as_read(notification)

    if notification.url and url_has_allowed_host_and_scheme(
        notification.url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(notification.url)

    return redirect("notifications:list")


@require_POST
@login_required
def notification_mark_all_read(request):
    user = cast(User, request.user)

    updated = mark_all_notifications_as_read(user)

    if updated:
        messages.success(
            request,
            "All notifications were marked as read.",
        )

    return redirect("notifications:list")
