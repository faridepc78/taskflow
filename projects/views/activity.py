from typing import cast

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from accounts.models import Profile

from ..models import Activity


@login_required
def activity_list(request):
    user = cast(User, request.user)
    profile_ids = Profile.objects.filter(user=user).values_list("pk", flat=True)

    activities = (
        Activity.objects.filter(
            Q(actor=user)
            | Q(project__owner=user)
            | Q(subject_type="auth.User", subject_id=str(user.pk))
            | Q(
                subject_type="accounts.Profile",
                subject_id__in=[str(pk) for pk in profile_ids],
            )
        )
        .select_related("actor", "project", "task")
        .distinct()
    )

    page = Paginator(activities, 50).get_page(request.GET.get("page"))
    return render(request, "projects/activity_list.html", {"page": page})
