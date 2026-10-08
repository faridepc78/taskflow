from datetime import timedelta

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from projects.models import Project, Task

from ..models import Notification
from ..services import create_deadline_notifications

TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "taskflow-notification-tests",
    }
}


@override_settings(CACHES=TEST_CACHES)
class NotificationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="user", password="Pass12345!")
        self.other = User.objects.create_user(username="other", password="Pass12345!")

    def test_user_only_sees_own_notifications(self):
        own = Notification.objects.create(
            user=self.user,
            title="Own",
            message="Own notification",
        )
        Notification.objects.create(
            user=self.other,
            title="Other",
            message="Other notification",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("notifications:list"))
        notifications = list(response.context["page_obj"].object_list)

        self.assertIn(own, notifications)
        self.assertEqual(len(notifications), 1)

    def test_user_cannot_mark_another_users_notification_as_read(self):
        notification = Notification.objects.create(
            user=self.other,
            title="Other",
            message="Private",
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("notifications:mark-read", args=[notification.pk])
        )

        self.assertEqual(response.status_code, 404)
        notification.refresh_from_db()
        self.assertFalse(notification.is_read)

    def test_mark_all_read_only_updates_current_user(self):
        own = Notification.objects.create(user=self.user, title="Own", message="Own")
        other = Notification.objects.create(
            user=self.other, title="Other", message="Other"
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("notifications:mark-all-read"))

        self.assertRedirects(response, reverse("notifications:list"))
        own.refresh_from_db()
        other.refresh_from_db()
        self.assertTrue(own.is_read)
        self.assertFalse(other.is_read)

    def test_deadline_notifications_create_expected_types_and_deduplicate(self):
        today = timezone.localdate()
        project = Project.objects.create(name="Project", owner=self.user)
        Task.objects.create(
            project=project,
            title="Tomorrow",
            due_date=today + timedelta(days=1),
        )
        Task.objects.create(project=project, title="Today", due_date=today)
        Task.objects.create(
            project=project,
            title="Overdue",
            due_date=today - timedelta(days=1),
        )

        first = create_deadline_notifications(current_date=today)
        second = create_deadline_notifications(current_date=today)

        self.assertEqual(first, {"reminder": 1, "deadline": 1, "overdue": 1})
        self.assertEqual(second, {"reminder": 0, "deadline": 0, "overdue": 0})
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 3)

    def test_deadline_notifications_ignore_done_and_archived_tasks(self):
        today = timezone.localdate()
        active_project = Project.objects.create(name="Active", owner=self.user)
        archived_project = Project.objects.create(
            name="Archived",
            owner=self.user,
            is_archived=True,
        )
        Task.objects.create(
            project=active_project,
            title="Done",
            due_date=today,
            status=Task.Status.DONE,
        )
        Task.objects.create(
            project=archived_project,
            title="Archived task",
            due_date=today,
        )

        result = create_deadline_notifications(current_date=today)

        self.assertEqual(result, {"reminder": 0, "deadline": 0, "overdue": 0})
        self.assertFalse(Notification.objects.exists())
