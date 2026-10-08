from typing import cast

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import CategoryForm
from ..models import Category


@login_required
def category_list(request):
    user = cast(User, request.user)
    categories = Category.objects.filter(owner=user).order_by("name")
    page_obj = Paginator(categories, 20).get_page(request.GET.get("page"))

    return render(
        request,
        "projects/category_list.html",
        {
            "page_obj": page_obj,
        },
    )


@transaction.atomic
@login_required
def category_create(request):
    user = cast(User, request.user)

    if request.method == "POST":
        form = CategoryForm(request.POST)

        if form.is_valid():
            category = form.save(commit=False)
            category.owner = user
            category.save()

            return redirect("projects:category-list")
    else:
        form = CategoryForm()

    return render(
        request,
        "projects/category_form.html",
        {
            "form": form,
            "title": "Create category",
        },
    )


@transaction.atomic
@login_required
def category_update(request, pk):
    user = cast(User, request.user)
    category = get_object_or_404(
        Category,
        pk=pk,
        owner=user,
    )

    if request.method == "POST":
        form = CategoryForm(
            request.POST,
            instance=category,
        )

        if form.is_valid():
            form.save()

            return redirect("projects:category-list")
    else:
        form = CategoryForm(instance=category)

    return render(
        request,
        "projects/category_form.html",
        {
            "form": form,
            "title": "Edit category",
            "category": category,
        },
    )


@transaction.atomic
@login_required
def category_delete(request, pk):
    user = cast(User, request.user)
    category = get_object_or_404(
        Category,
        pk=pk,
        owner=user,
    )

    if request.method == "POST":
        category.delete()

        return redirect("projects:category-list")

    return render(
        request,
        "projects/category_confirm_delete.html",
        {
            "category": category,
        },
    )
