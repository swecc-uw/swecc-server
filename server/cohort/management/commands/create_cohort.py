from cohort.models import Cohort
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Initialize a cohort"

    def add_arguments(self, parser):
        parser.add_argument("--name", type=str, help="Cohort Name")

    def handle(self, *args, **options):
        name = options["name"]

        if not name:
            self.stdout.write(self.style.ERROR("Cohort name is required"))
            return

        created_cohort, _ = Cohort.objects.get_or_create(name=name)
        created_cohort.save()

        self.stdout.write(self.style.SUCCESS(f"Cohort {created_cohort.name} created"))
