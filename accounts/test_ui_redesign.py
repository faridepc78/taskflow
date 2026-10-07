"""Presentation regressions. No external SMTP, broker, or cache is needed."""

from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.template.loader import get_template
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from projects.models import Category, Project, Task

from .models import Profile
from .tasks import send_otp_email_task, send_password_reset_otp_email_task

TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "taskflow-ui-tests",
    }
}


@override_settings(
    CACHES=TEST_CACHES,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class RedesignPageTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="ui_review_owner",
            email="ui-review@example.com",
            password="UiReviewPassword123!",
        )
        Profile.objects.create(user=self.user)
        self.project = Project.objects.create(name="UI review project", owner=self.user)
        self.task = Task.objects.create(title="UI review task", project=self.project)
        self.category = Category.objects.create(name="UI review", owner=self.user)
        self.client.force_login(self.user)

    def test_all_project_templates_compile(self):
        template_root = Path(settings.BASE_DIR) / "templates"
        for path in template_root.rglob("*.html"):
            name = path.relative_to(template_root).as_posix()
            with self.subTest(template=name):
                self.assertIsNotNone(get_template(name))

    def test_workspace_pages_render_with_shared_navigation(self):
        names = (
            "projects:dashboard",
            "projects:category-list",
            "projects:category-create",
            "projects:archived",
            "projects:activity-list",
            "projects:create",
            "notifications:list",
            "accounts:profile",
            "accounts:change-password",
        )
        for name in names:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'id="workspace-sidebar"')
                self.assertContains(response, reverse("accounts:logout"))
                self.assertNotContains(response, "bootstrap.min.css")

    def test_object_pages_still_resolve_the_original_routes(self):
        routes = (
            ("projects:detail", self.project.pk),
            ("projects:update", self.project.pk),
            ("projects:delete", self.project.pk),
            ("projects:task-create", self.project.pk),
            ("projects:task-update", self.task.pk),
            ("projects:task-delete", self.task.pk),
            ("projects:attachment-upload", self.task.pk),
            ("projects:category-update", self.category.pk),
            ("projects:category-delete", self.category.pk),
        )
        for name, pk in routes:
            with self.subTest(page=name):
                response = self.client.get(reverse(name, args=[pk]))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "csrfmiddlewaretoken")

    def test_task_form_preserves_all_field_names(self):
        response = self.client.get(reverse("projects:task-update", args=[self.task.pk]))
        for name in (
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "categories",
        ):
            with self.subTest(field=name):
                self.assertContains(response, f'name="{name}"')

    def test_profile_and_attachment_forms_keep_multipart_encoding(self):
        urls = (
            reverse("accounts:profile"),
            reverse("projects:attachment-upload", args=[self.task.pk]),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'enctype="multipart/form-data"')

    def test_board_preserves_status_endpoint_and_progress_hooks(self):
        response = self.client.get(reverse("projects:detail", args=[self.project.pk]))
        for marker in (
            'id="kanban-board"',
            'id="project-progress-bar"',
            'id="project-progress-count"',
            'data-status="todo"',
            'data-status="in_progress"',
            'data-status="done"',
            reverse("projects:task-change-status", args=[self.task.pk]),
        ):
            with self.subTest(marker=marker):
                self.assertContains(response, marker)

    def test_public_forms_preserve_fields_and_csrf(self):
        client = Client()
        cases = (
            ("accounts:login", ("username", "password")),
            (
                "accounts:register",
                (
                    "first_name",
                    "last_name",
                    "username",
                    "email",
                    "password",
                    "password_confirm",
                ),
            ),
            ("accounts:forgot-password", ("email",)),
        )
        for name, fields in cases:
            with self.subTest(page=name):
                response = client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "csrfmiddlewaretoken")
                for field in fields:
                    self.assertContains(response, f'name="{field}"')

    def test_verification_forms_keep_post_resend_actions(self):
        client = Client()
        session = client.session
        session["pending_registration"] = {"email": "pending@example.com"}
        session["password_reset_email"] = self.user.email
        session.save()
        cases = (
            ("accounts:verify-email", "accounts:resend-verification-code"),
            ("accounts:verify-password-reset", "accounts:resend-password-reset-code"),
        )
        for name, resend in cases:
            with self.subTest(page=name):
                response = client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'name="code"')
                self.assertContains(response, f'action="{reverse(resend)}"')


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class RedesignEmailTests(SimpleTestCase):
    def test_registration_email_keeps_plaintext_and_adds_html(self):
        send_otp_email_task.run("preview@example.com", "123456")
        message = mail.outbox[-1]
        self.assertEqual(message.subject, "Verify your email")
        self.assertEqual(message.to, ["preview@example.com"])
        self.assertEqual(message.body, "Your verification code is: 123456")
        self.assertEqual(message.alternatives[0][1], "text/html")
        self.assertIn("123456", message.alternatives[0][0])

    def test_reset_email_keeps_plaintext_and_adds_html(self):
        send_password_reset_otp_email_task.run("preview@example.com", "654321")
        message = mail.outbox[-1]
        self.assertEqual(message.subject, "Reset your TaskFlow password")
        self.assertEqual(message.to, ["preview@example.com"])
        self.assertEqual(message.body, "Your password reset code is: 654321")
        self.assertEqual(message.alternatives[0][1], "text/html")
        self.assertIn("654321", message.alternatives[0][0])
