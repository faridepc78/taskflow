from typing import ClassVar

from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    class Kind(models.TextChoices):
        INFO = "info", "Info"
        DEADLINE = "deadline", "Deadline"
        REMINDER = "reminder", "Reminder"
        OVERDUE = "overdue", "Overdue"
        SYSTEM = "system", "System"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.INFO,
    )
    title = models.CharField(max_length=200)
    message = models.CharField(max_length=500)
    url = models.CharField(max_length=500, blank=True)
    deduplication_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=("user", "deduplication_key"),
                name="uniq_notification_user_dedupe",
            ),
        ]
        indexes: ClassVar = [
            models.Index(
                fields=("user", "is_read", "created_at"),
                name="notification_user_read_idx",
            ),
            models.Index(
                fields=("kind", "created_at"),
                name="notification_kind_date_idx",
            ),
        ]

    def mark_as_read(self) -> None:
        if self.is_read:
            return

        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=("is_read", "read_at"))

    def __str__(self):
        return self.title
