from django.core.management.base import BaseCommand

from accounts.models import Customer, User


class Command(BaseCommand):
    help = "Create a superuser and a regular user for development"

    def handle(self, *args, **options):
        self._create_superuser()
        self._create_regular_user()

    def _create_superuser(self):
        email = "admin@signals.dev"
        password = "admin"

        if User.objects.filter(email=email).exists():
            self.stdout.write(f"Superuser {email} already exists, skipping.")
            return

        User.objects.create_superuser(email=email, password=password, first_name="Admin", last_name="Signals")
        self.stdout.write(self.style.SUCCESS(f"Superuser created: {email} / {password}"))

    def _create_regular_user(self):
        email = "user@signals.dev"
        password = "user"

        if User.objects.filter(email=email).exists():
            self.stdout.write(f"User {email} already exists, skipping.")
            return

        user = User.objects.create_user(email=email, password=password, first_name="Jean", last_name="Dupont")
        Customer.objects.create(user=user)
        self.stdout.write(self.style.SUCCESS(f"Regular user created:  {email} / {password}"))
