from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from ..models import Activity, Category, Project, Task


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class DeleteRegressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="deleteuser", password="Pass12345!"
        )
        self.client.force_login(self.user)
        self.project = Project.objects.create(name="Project to delete", owner=self.user)
        self.task = Task.objects.create(project=self.project, title="Task to delete")

    def test_delete_project_cascades_tasks_and_keeps_history(self):
        pk = self.project.pk
        response = self.client.post(reverse("projects:delete", args=[pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Project.objects.filter(pk=pk).exists())
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())
        self.assertTrue(
            Activity.objects.filter(
                subject_type="projects.Task",
                subject_id=str(self.task.pk),
                action="deleted",
                project__isnull=True,
                task__isnull=True,
            ).exists()
        )
        self.assertTrue(
            Activity.objects.filter(
                subject_type="projects.Project", subject_id=str(pk), action="deleted"
            ).exists()
        )
        self.assertFalse(
            Activity.objects.exclude(project__isnull=True)
            .filter(subject_id=str(pk), subject_type="projects.Project")
            .exists()
        )

    def test_delete_task_keeps_history(self):
        pk = self.task.pk
        response = self.client.post(reverse("projects:task-delete", args=[pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Activity.objects.filter(
                subject_type="projects.Task", subject_id=str(pk), action="deleted"
            ).exists()
        )

    def test_delete_category_keeps_tasks(self):
        category = Category.objects.create(owner=self.user, name="Test")
        self.task.categories.add(category)
        response = self.client.post(
            reverse("projects:category-delete", args=[category.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())
        self.assertTrue(
            Activity.objects.filter(
                subject_type="projects.Category",
                subject_id=str(category.pk),
                action="deleted",
            ).exists()
        )
