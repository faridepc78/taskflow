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
    name = models.CharField(max_length=100, unique=True)

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
