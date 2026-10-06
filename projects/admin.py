from django.contrib import admin

from .models import Activity, Category, Project, Task, TaskAttachment


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


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "action",
        "subject_type",
        "subject_name",
        "actor",
        "project",
        "created_at",
    )
    list_filter = ("action", "subject_type", "created_at")
    search_fields = (
        "description",
        "subject_name",
        "actor__username",
        "project__name",
        "task__title",
    )
    readonly_fields = (
        "project",
        "task",
        "actor",
        "action",
        "subject_type",
        "subject_id",
        "subject_name",
        "description",
        "changes",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
