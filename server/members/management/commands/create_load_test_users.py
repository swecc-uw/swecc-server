from members.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Command to create n test users with discord ids from start to n + start"

    def add_arguments(self, parser):
        parser.add_argument(
            "--n", type=int, help="number of test users to create", default=10
        )
        parser.add_argument("--start", type=int, help="starting discord id", default=1)

        return super().add_arguments(parser)

    def handle(self, *args, **options):
        created = []
        n = options["n"]
        start = options["start"]
        for i in range(start, n + start):
            u = User.objects.create(
                username=f"testuser{i}",
                email=f"user{i}@test.com",
                discord_id=str(i),
                first_name=f"Test{i}_First",
                last_name=f"Test{i}_Last",
                preview=f"{i}th test account or load testing",
                major="Computer Science",
                grad_date="2022-06-01",
                discord_username=f"testuser{i}",
                local="San Francisco",
                bio=f"Test{i} bio",
            )

            created.append(u)


        self.stdout.write(self.style.SUCCESS(f"Created {n} test users"))
        self.stdout.write(f"discord_ids: {', '.join([str(u.discord_id) for u in created])}")