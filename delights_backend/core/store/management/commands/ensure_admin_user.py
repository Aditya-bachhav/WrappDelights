from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


# Hardcoded bootstrap credentials for the admin account.
# Username: admin
# Password: D^L!G#t$0@dm/7404
# Email: admin@example.com
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "D^L!G#t$0@dm/7404"
ADMIN_EMAIL = "admin@example.com"


class Command(BaseCommand):
    help = "Bootstrap admin superuser with hardcoded credentials."

    def handle(self, *args, **options):
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=ADMIN_USERNAME,
            defaults={
                "email": ADMIN_EMAIL,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        # Enforce credentials on every run.
        user.email = ADMIN_EMAIL
        user.is_staff = True
        user.is_superuser = True
        user.set_password(ADMIN_PASSWORD)
        user.save()

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(f"Admin superuser '{ADMIN_USERNAME}' {action}.")
        )