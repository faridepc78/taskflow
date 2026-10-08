from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed default application data."

    def handle(self, *args, **options):
        User = get_user_model()

        first_name = "farid"
        last_name = "shishebori"
        username = "faridepc78"
        email = "faridnewepc78@gmail.com"
        password = "1234f01234"

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser "{username}" already exists. Skipped.')
            )
            return

        User.objects.create_superuser(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,
        )

        self.stdout.write(
            self.style.SUCCESS(f'Superuser "{username}" created successfully.')
        )
