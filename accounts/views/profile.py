from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from ..forms import ProfileForm
from ..models import Profile


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
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=profile_instance, user=user)

    return render(
        request,
        "accounts/profile.html",
        {"form": form, "profile": profile_instance},
    )
