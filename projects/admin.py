from django.contrib import admin

from .models import Category, Project, Task, TaskAttachment


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "is_archived",
        "created_at",
    )

    list_filter = (
        "is_archived",
        "created_at",
    )

    search_fields = (
        "name",
        "owner__username",
        "owner__email",
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "status",
        "priority",
        "due_date",
        "created_at",
    )

    list_filter = (
        "status",
        "priority",
        "due_date",
    )

    search_fields = (
        "title",
        "project__name",
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "filename",
        "task",
        "uploaded_at",
    )
    search_fields = (
        "file",
        "task__title",
        "task__project__name",
    )
