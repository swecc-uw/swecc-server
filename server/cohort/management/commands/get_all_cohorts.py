from cohort.models import Cohort
from cohort.serializers import CohortSerializer
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = "List all cohorts"

    def handle(self, *args, **options):

        all_cohorts = Cohort.objects.all()

        for cohort in all_cohorts:
            self.stdout.write(self.style.SUCCESS(f"{CohortSerializer(cohort).data}"))
