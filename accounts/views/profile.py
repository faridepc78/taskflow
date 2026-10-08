import mimetypes
from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render

from ..forms import ProfileForm
from ..models import Profile


@transaction.atomic
@login_required
def profile(request):
    user = cast(User, request.user)
    profile_instance, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile_instance,
            user=user,
        )

        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                form.add_error("email", "This email is no longer available.")
            else:
                messages.success(request, "Your profile has been updated successfully.")
                return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=profile_instance, user=user)

    return render(
        request,
        "accounts/profile.html",
        {"form": form, "profile": profile_instance},
    )


@login_required
def avatar_view(request):
    profile_obj = Profile.objects.filter(user=request.user).first()
    if not profile_obj or not profile_obj.avatar:
        raise Http404("Avatar not found.")
    try:
        stream = profile_obj.avatar.open("rb")
    except (FileNotFoundError, OSError) as exc:
        raise Http404("Avatar not found.") from exc
    response = FileResponse(stream, content_type=mimetypes.guess_type(profile_obj.avatar.name)[0] or "application/octet-stream")
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response
