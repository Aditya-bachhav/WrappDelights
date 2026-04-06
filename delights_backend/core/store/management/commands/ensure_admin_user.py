from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


ADMIN_USERNAME = "Admin"
ADMIN_PASSWORD = "D^L!G#t$0@dm/7404"
ADMIN_EMAIL = "admin@example.com"


class Command(BaseCommand):
    help = "Ensure the fixed Admin superuser exists with expected credentials."

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

        # Enforce fixed credentials and privileges on every run.
        user.username = ADMIN_USERNAME
        user.email = ADMIN_EMAIL
        user.is_staff = True
        user.is_superuser = True
        user.set_password(ADMIN_PASSWORD)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS("Created fixed Admin superuser."))
        else:
            self.stdout.write(self.style.SUCCESS("Updated fixed Admin superuser credentials."))