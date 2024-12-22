from members.models import User
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from os import environ

class Command(BaseCommand):
    verify_account = 'Verify User account'

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, help="SWECC Interview Website Username")
        parser.add_argument("--discord_id", type=str, help="User's Discord ID")

    def handle(self, *args, **options):
        DJANGO_DEBUG = os.environ['DJANGO_DEBUG']
        if not DJANGO_DEBUG:
            self.stdout.write(self.style.ERROR(f'This command is ONLY allowed in development mode.'))
            return
        username = options['username']
        new_discord_id = options['discord_id']

        member = User.objects.filter(username=username).first()
        if member is None:
            self.stdout.write(self.style.ERROR(f'Username {username} was not found!'))
            return

        member.discord_id = new_discord_id
        member.save()

        is_verified_groups, _ = Group.objects.get_or_create(name="is_verified")
        member.groups.add(is_verified_groups)

        self.stdout.write(self.style.SUCCESS(f'Verified Username: {username} Discord ID: {new_discord_id}'))

