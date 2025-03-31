from cohort.models import Cohort
from django.core.management.base import BaseCommand
from engagement.models import CohortStats
from engagement.serializers import CohortStatsSerializer
from members.models import User


class Command(BaseCommand):
    help = "Add a user to a cohort, and create a CohortStats object for the user"

    def add_arguments(self, parser):
        parser.add_argument("--cohort-name", type=str, help="Cohort Name")
        parser.add_argument(
            "--username", type=str, help="Username of the user to add to the cohort"
        )

    def handle(self, *args, **options):

        cohort_name = options["cohort_name"]
        username = options["username"]

        if not cohort_name:
            self.stdout.write(self.style.ERROR("Cohort name is required"))
            return

        if not username:
            self.stdout.write(self.style.ERROR("Username is required"))
            return

        cohort = Cohort.objects.filter(name=cohort_name).first()
        if cohort is None:
            self.stdout.write(self.style.ERROR(f"Cohort {cohort_name} was not found!"))
            return

        user = User.objects.filter(username=username).first()
        if user is None:
            self.stdout.write(self.style.ERROR(f"Username {username} was not found!"))
            return

        if not cohort.members.filter(username=username).exists():
            cohort.members.add(user)

        cohort_stats = CohortStats.objects.get_or_create(cohort=cohort, member=user)[0]

        self.stdout.write(
            self.style.SUCCESS(
                f"Cohort Stats {CohortStatsSerializer(cohort_stats).data} created"
            )
        )

        cohort.save()

        self.stdout.write(
            self.style.SUCCESS(f"Added {user.username} to cohort {cohort.name}")
        )
