from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("activity/", views.activity_list, name="activity-list"),
    path("projects/create/", views.project_create, name="create"),
    path("projects/archived/", views.archived_projects, name="archived"),
    path("projects/<int:pk>/", views.project_detail, name="detail"),
    path("projects/<int:pk>/edit/", views.project_update, name="update"),
    path("projects/<int:pk>/delete/", views.project_delete, name="delete"),
    path("projects/<int:pk>/archive/", views.project_archive, name="archive"),
    path("projects/<int:pk>/restore/", views.project_restore, name="restore"),
    path(
        "projects/<int:project_pk>/tasks/create/",
        views.task_create,
        name="task-create",
    ),
    path("tasks/<int:pk>/edit/", views.task_update, name="task-update"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task-delete"),
    path(
        "tasks/<int:task_pk>/attachments/upload/",
        views.attachment_upload,
        name="attachment-upload",
    ),
    path(
        "attachments/<int:pk>/delete/",
        views.attachment_delete,
        name="attachment-delete",
    ),
    path(
        "attachments/<int:pk>/download/",
        views.attachment_download,
        name="attachment-download",
    ),
    path(
        "tasks/<int:pk>/status/",
        views.task_change_status,
        name="task-change-status",
    ),
    path("categories/", views.category_list, name="category-list"),
    path("categories/create/", views.category_create, name="category-create"),
    path(
        "categories/<int:pk>/edit/",
        views.category_update,
        name="category-update",
    ),
    path(
        "categories/<int:pk>/delete/",
        views.category_delete,
        name="category-delete",
    ),
]
