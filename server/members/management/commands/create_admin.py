from members.models import User
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Add user to admin group'

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, help="SWECC Interview Website Username")

    def handle(self, *args, **options):

        username = options['username']

        member = User.objects.get(username=username)

        is_verified_groups, _ = Group.objects.get_or_create(name="is_admin")
        member.groups.add(is_verified_groups)

        self.stdout.write(self.style.SUCCESS(f'Added to admin group - username: {username}'))

