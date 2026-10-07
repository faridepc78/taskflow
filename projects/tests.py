from datetime import timedelta
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Category, Project, Task, TaskAttachment

TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "taskflow-project-tests",
    }
}


@override_settings(CACHES=TEST_CACHES)
class ProjectOwnershipTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username="owner", password="Pass12345!")
        self.other = User.objects.create_user(username="other", password="Pass12345!")
        self.project = Project.objects.create(name="Owner project", owner=self.owner)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("projects:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_user_cannot_view_another_users_project(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("projects:detail", args=[self.project.pk]))
        self.assertEqual(response.status_code, 404)

    def test_project_create_sets_logged_in_user_as_owner(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("projects:create"),
            {"name": "New project", "description": "Description"},
        )

        project = Project.objects.get(name="New project")
        self.assertEqual(project.owner, self.owner)
        self.assertRedirects(response, reverse("projects:detail", args=[project.pk]))

    def test_archive_and_restore_project(self):
        self.client.force_login(self.owner)

        archive_response = self.client.post(
            reverse("projects:archive", args=[self.project.pk])
        )
        self.project.refresh_from_db()
        self.assertTrue(self.project.is_archived)
        self.assertRedirects(archive_response, reverse("projects:dashboard"))

        restore_response = self.client.post(
            reverse("projects:restore", args=[self.project.pk])
        )
        self.project.refresh_from_db()
        self.assertFalse(self.project.is_archived)
        self.assertRedirects(restore_response, reverse("projects:archived"))


@override_settings(CACHES=TEST_CACHES)
class TaskAndCategoryTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username="owner", password="Pass12345!")
        self.other = User.objects.create_user(username="other", password="Pass12345!")
        self.project = Project.objects.create(name="Project", owner=self.owner)
        self.other_project = Project.objects.create(name="Other", owner=self.other)
        self.category = Category.objects.create(owner=self.owner, name="Backend")
        self.other_category = Category.objects.create(owner=self.other, name="Private")
        self.task = Task.objects.create(
            project=self.project,
            title="Task",
            status=Task.Status.TODO,
            priority=Task.Priority.HIGH,
        )

    def test_task_create_uses_only_owners_project(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("projects:task-create", args=[self.project.pk]),
            {
                "title": "Hacked task",
                "description": "",
                "status": Task.Status.TODO,
                "priority": Task.Priority.MEDIUM,
                "due_date": "",
            },
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Task.objects.filter(title="Hacked task").exists())

    def test_task_status_change_updates_progress(self):
        self.client.force_login(self.owner)
        Task.objects.create(project=self.project, title="Second")

        response = self.client.post(
            reverse("projects:task-change-status", args=[self.task.pk]),
            {"status": Task.Status.DONE},
        )

        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.DONE)
        self.assertEqual(response.json()["progress_percentage"], 50)

    def test_task_status_change_rejects_invalid_status(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("projects:task-change-status", args=[self.task.pk]),
            {"status": "invalid"},
        )
        self.assertEqual(response.status_code, 400)

    def test_category_update_is_owner_only(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("projects:category-update", args=[self.category.pk]),
            {"name": "Changed"},
        )
        self.assertEqual(response.status_code, 404)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Backend")

    def test_task_form_does_not_accept_another_users_category(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("projects:task-create", args=[self.project.pk]),
            {
                "title": "Categorized task",
                "description": "",
                "status": Task.Status.TODO,
                "priority": Task.Priority.MEDIUM,
                "due_date": "",
                "categories": [self.other_category.pk],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(title="Categorized task").exists())

    def test_deadline_filters_overdue_tasks(self):
        today = timezone.localdate()
        overdue = Task.objects.create(
            project=self.project,
            title="Overdue",
            due_date=today - timedelta(days=1),
        )
        Task.objects.create(
            project=self.project,
            title="Upcoming",
            due_date=today + timedelta(days=2),
        )
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("projects:detail", args=[self.project.pk]),
            {"deadline": "overdue"},
        )

        tasks = list(response.context["tasks"])
        self.assertIn(overdue, tasks)
        self.assertEqual(len(tasks), 1)


@override_settings(CACHES=TEST_CACHES)
class AttachmentOwnershipTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username="owner", password="Pass12345!")
        self.other = User.objects.create_user(username="other", password="Pass12345!")
        self.project = Project.objects.create(name="Project", owner=self.owner)
        self.task = Task.objects.create(project=self.project, title="Task")

    def test_attachment_upload_and_delete(self):
        with (
            TemporaryDirectory() as media_root,
            override_settings(MEDIA_ROOT=media_root),
        ):
            self.client.force_login(self.owner)
            upload = SimpleUploadedFile("note.txt", b"hello", content_type="text/plain")

            response = self.client.post(
                reverse("projects:attachment-upload", args=[self.task.pk]),
                {"file": upload},
            )

            self.assertRedirects(
                response,
                reverse("projects:detail", args=[self.project.pk]),
            )
            attachment = TaskAttachment.objects.get(task=self.task)

            delete_response = self.client.post(
                reverse("projects:attachment-delete", args=[attachment.pk])
            )
            self.assertRedirects(
                delete_response,
                reverse("projects:detail", args=[self.project.pk]),
            )
            self.assertFalse(TaskAttachment.objects.filter(pk=attachment.pk).exists())

    def test_other_user_cannot_delete_attachment(self):
        attachment = TaskAttachment.objects.create(
            task=self.task, file="task_attachments/a.txt"
        )
        self.client.force_login(self.other)

        response = self.client.post(
            reverse("projects:attachment-delete", args=[attachment.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(TaskAttachment.objects.filter(pk=attachment.pk).exists())
