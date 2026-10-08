from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ..forms import CategoryForm, ProjectForm, TaskForm
from ..models import Category, Task


class ValidationRegressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="validator", password="SafePass123!"
        )
        self.other = User.objects.create_user(
            username="another", password="SafePass123!"
        )
        self.client.force_login(self.user)

    def test_duplicate_category_create_displays_field_error(self):
        Category.objects.create(owner=self.user, name="Management")
        response = self.client.post(
            reverse("projects:category-create"), {"name": "Management"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A category with this name already exists.")
        self.assertEqual(Category.objects.filter(owner=self.user).count(), 1)

    def test_duplicate_category_update_displays_field_error(self):
        Category.objects.create(owner=self.user, name="Management")
        category = Category.objects.create(owner=self.user, name="Operations")
        response = self.client.post(
            reverse("projects:category-update", args=[category.pk]),
            {"name": "Management"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A category with this name already exists.")
        category.refresh_from_db()
        self.assertEqual(category.name, "Operations")

    def test_category_names_are_scoped_to_owner(self):
        Category.objects.create(owner=self.other, name="Management")
        form = CategoryForm({"name": "Management"}, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_category_whitespace_is_normalized(self):
        form = CategoryForm({"name": "  Management  "}, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["name"], "Management")

    def test_project_name_cannot_be_whitespace(self):
        self.assertFalse(ProjectForm({"name": "   "}).is_valid())

    def test_task_title_cannot_be_whitespace(self):
        form = TaskForm(
            {
                "title": "   ",
                "status": Task.Status.TODO,
                "priority": Task.Priority.MEDIUM,
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())

    def test_task_rejects_another_users_category(self):
        category = Category.objects.create(owner=self.other, name="Private")
        form = TaskForm(
            {
                "title": "Example",
                "status": Task.Status.TODO,
                "priority": Task.Priority.MEDIUM,
                "categories": [category.pk],
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())
