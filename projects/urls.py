from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path(
        "projects/create/",
        views.project_create,
        name="create",
    ),
    path(
        "projects/<int:pk>/",
        views.project_detail,
        name="detail",
    ),
    path(
        "projects/<int:pk>/edit/",
        views.project_update,
        name="update",
    ),
    path(
        "projects/<int:pk>/delete/",
        views.project_delete,
        name="delete",
    ),
    path(
        "projects/<int:project_pk>/tasks/create/",
        views.task_create,
        name="task-create",
    ),
    path(
        "tasks/<int:pk>/edit/",
        views.task_update,
        name="task-update",
    ),
    path(
        "tasks/<int:pk>/delete/",
        views.task_delete,
        name="task-delete",
    ),
]
