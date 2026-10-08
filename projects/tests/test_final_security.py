from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from ..forms import TaskAttachmentForm
from ..models import Project, Task, TaskAttachment


class ArchiveAndAttachmentSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="secure", password="SafeStrong123!")
        self.other = User.objects.create_user(username="outsider", password="SafeStrong123!")
        self.project = Project.objects.create(owner=self.user, name="Archived", is_archived=True)
        self.task = Task.objects.create(project=self.project, title="Existing")
        self.client.force_login(self.user)

    def test_archived_project_denies_all_mutations(self):
        cases = [
            ("projects:update", [self.project.pk], {"name": "Changed"}),
            ("projects:delete", [self.project.pk], {}),
            ("projects:task-create", [self.project.pk], {"title": "New"}),
            ("projects:task-update", [self.task.pk], {"title": "Updated"}),
            ("projects:task-delete", [self.task.pk], {}),
            ("projects:task-change-status", [self.task.pk], {"status": "done"}),
            ("projects:attachment-upload", [self.task.pk], {}),
        ]
        for name, args, data in cases:
            with self.subTest(name=name):
                response = self.client.post(reverse(name, args=args), data)
                self.assertEqual(response.status_code, 404)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "todo")
        self.assertEqual(Task.objects.filter(project=self.project).count(), 1)

    def test_archive_page_does_not_offer_edit_controls(self):
        response = self.client.get(reverse("projects:detail", args=[self.project.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "New task")
        self.assertContains(response, "Restore")

    def test_bad_attachment_type_is_rejected(self):
        upload = SimpleUploadedFile("run.html", b"<script>alert(1)</script>")
        self.assertFalse(TaskAttachmentForm(files={"file": upload}).is_valid())

    def test_download_is_restricted_to_owner(self):
        attachment = TaskAttachment.objects.create(task=self.task, file="task_attachments/test.pdf")
        self.client.force_login(self.other)
        response = self.client.get(reverse("projects:attachment-download", args=[attachment.pk]))
        self.assertEqual(response.status_code, 404)
