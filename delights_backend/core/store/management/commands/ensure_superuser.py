import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or update a superuser from environment variables."

    def handle(self, *args, **options):
        username = (
            os.getenv("ADMIN_BOOTSTRAP_USERNAME")
            or os.getenv("DJANGO_SUPERUSER_USERNAME")
            or ""
        ).strip()
        password = (
            os.getenv("ADMIN_BOOTSTRAP_PASSWORD")
            or os.getenv("DJANGO_SUPERUSER_PASSWORD")
            or ""
        ).strip()
        email = (
            os.getenv("ADMIN_BOOTSTRAP_EMAIL")
            or os.getenv("DJANGO_SUPERUSER_EMAIL")
            or "admin@example.com"
        ).strip()

        if not username or not password:
            raise CommandError(
                "ADMIN_BOOTSTRAP_USERNAME and ADMIN_BOOTSTRAP_PASSWORD must be set on the Render service."
            )

        user_model = get_user_model()
        user = user_model.objects.filter(username__iexact=username).first()

        created = False
        if not user:
            user = user_model(username=username)
            created = True

        user.username = username
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' updated."))
