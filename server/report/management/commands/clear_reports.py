import logging
import uuid
from django.core.management.base import BaseCommand
from report.models import Report


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Deletes all reports"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry",
            action="store_true",
            help="Dry run, don't actually delete reports",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Delete all reports",
        )
        parser.add_argument(
            "--username",
            type=str,
            help="Delete reports by user",
        )
        parser.add_argument(
            "--report_id",
            type=uuid.UUID,
            help="Delete report by ID",
        )
        parser.add_argument(
            "--status",
            type=str,
            help="Delete reports by status",
        )

    def handle(self, *args, **options):
        reports = Report.objects.all()

        if not options["all"]:
            if options["username"]:
                reports = reports.filter(reporter_user_id__username=options["username"])

            if options["report_id"]:
                reports = reports.filter(report_id=options["report_id"])

            if options["status"]:
                reports = reports.filter(status=options["status"])

        if options["dry"]:
            logger.info(f"Would delete {reports.count()} reports")
            return

        size = reports.count()
        reports.delete()
        logger.info(f"{size} reports deleted")
