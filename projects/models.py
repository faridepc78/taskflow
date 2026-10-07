from typing import ClassVar

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Project(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="projects",
    )

    is_archived = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="categories",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=("owner", "name"),
                name="unique_category_name_per_owner",
            )
        ]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    due_date = models.DateField(
        null=True,
        blank=True,
    )

    categories = models.ManyToManyField(
        Category,
        related_name="tasks",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def due_state(self) -> str:
        if not self.due_date:
            return "none"

        today = timezone.localdate()

        if self.due_date < today:
            return "overdue"

        if self.due_date == today:
            return "today"

        return "upcoming"

    @property
    def is_overdue(self) -> bool:
        return self.status != self.Status.DONE and self.due_state == "overdue"

    @property
    def is_due_today(self) -> bool:
        return self.status != self.Status.DONE and self.due_state == "today"

    def __str__(self):
        return self.title


class TaskAttachment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="task_attachments/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def filename(self) -> str:
        return self.file.name.rsplit("/", 1)[-1]

    def __str__(self):
        return self.filename


class Activity(models.Model):
    class Action(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        DELETED = "deleted", "Deleted"
        RELATION_CHANGED = "relation_changed", "Relation changed"

        # Backward-compatible names used by the first activity implementation.
        PROJECT_CREATED = "project_created", "Project created"
        PROJECT_UPDATED = "project_updated", "Project updated"
        PROJECT_ARCHIVED = "project_archived", "Project archived"
        PROJECT_RESTORED = "project_restored", "Project restored"
        TASK_CREATED = "task_created", "Task created"
        TASK_UPDATED = "task_updated", "Task updated"
        TASK_DELETED = "task_deleted", "Task deleted"
        TASK_STATUS_CHANGED = "task_status_changed", "Task status changed"
        ATTACHMENT_UPLOADED = "attachment_uploaded", "Attachment uploaded"
        ATTACHMENT_DELETED = "attachment_deleted", "Attachment deleted"

    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        related_name="activities",
        null=True,
        blank=True,
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        related_name="activities",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="taskflow_activities",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=40, choices=Action.choices)
    subject_type = models.CharField(max_length=100, blank=True)
    subject_id = models.CharField(max_length=100, blank=True)
    subject_name = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=500)
    changes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes: ClassVar = [
            models.Index(
                fields=("subject_type", "subject_id"),
                name="activity_subject_idx",
            ),
            models.Index(
                fields=("action", "created_at"),
                name="activity_action_date_idx",
            ),
        ]

    def __str__(self):
        return self.description
