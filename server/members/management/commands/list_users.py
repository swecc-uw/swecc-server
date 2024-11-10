from members.models import User
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Command to print out all users'

    def handle(self, *args, **options):
        pp = lambda user: f"Username: {user['username']}, Email: {user['email']}, Discord ID: {user['discord_id']}"

        for user in User.objects.all().values('username', 'email', 'discord_id'):
            self.stdout.write(self.style.SUCCESS(pp(user)))