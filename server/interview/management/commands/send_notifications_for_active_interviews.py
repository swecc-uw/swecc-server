from django.core.management.base import BaseCommand
from django.utils import timezone
from interview.models import Interview
import server.settings as settings
from django.db.models import Q
import logging

from interview.notification import interview_paired_notification_html
from email_util.send_email import send_email
from interview.views import INTERVIEW_NOTIFICATION_ADDR

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Resends email notifications for all pending interviews'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry',
            action='store_true',
            help='Perform a dry run without sending emails'
        )

    def handle(self, *args, **options):
        is_dry_run = options['dry']

        today = timezone.now()
        last_monday = today - timezone.timedelta(days=today.weekday())
        last_monday = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        next_next_monday = last_monday + timezone.timedelta(days=14)

        pending_interviews = Interview.objects.filter(
            date_effective__gte=last_monday, date_effective__lte=next_next_monday
        )

        if not pending_interviews.exists():
            self.stdout.write(
                self.style.WARNING("No pending interviews found")
            )
            return

        self.stdout.write(f"Found {pending_interviews.count()} pending interviews")
        failed_emails = []

        if not is_dry_run:
            self.stdout.write(
                self.style.WARNING("\nThis is a live run - sending notifications...")
            )

            for interview in pending_interviews:
                # send to interviewer
                try:
                    send_email(
                        from_email=INTERVIEW_NOTIFICATION_ADDR,
                        to_email=interview.interviewer.email,
                        subject="You've been paired for an upcoming mock interview!",
                        html_content=interview_paired_notification_html(
                            name=interview.interviewer.first_name,
                            partner_name=interview.interviewee.first_name,
                            partner_email=interview.interviewee.email,
                            partner_discord_id=interview.interviewee.discord_id,
                            partner_discord_username=interview.interviewee.discord_username,
                            interview_date=interview.date_effective,
                        ),
                    )
                except Exception as e:
                    failed_emails.append(
                        (str(interview.interview_id), interview.interviewer.email, str(e))
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to send notification to interviewer {interview.interviewer.email}: {str(e)}"
                        )
                    )

                # send to interviewee
                try:
                    send_email(
                        from_email=INTERVIEW_NOTIFICATION_ADDR,
                        to_email=interview.interviewee.email,
                        subject="You've been paired for an upcoming mock interview!",
                        html_content=interview_paired_notification_html(
                            name=interview.interviewee.first_name,
                            partner_name=interview.interviewer.first_name,
                            partner_email=interview.interviewer.email,
                            partner_discord_id=interview.interviewer.discord_id,
                            partner_discord_username=interview.interviewer.discord_username,
                            interview_date=interview.date_effective,
                        ),
                    )
                except Exception as e:
                    failed_emails.append(
                        (str(interview.interview_id), interview.interviewee.email, str(e))
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to send notification to interviewee {interview.interviewee.email}: {str(e)}"
                        )
                    )

            if failed_emails:
                self.stdout.write(
                    self.style.ERROR(f"\nFailed to send {len(failed_emails)} notifications:")
                )
                for interview_id, email, error in failed_emails:
                    self.stdout.write(f"  - Interview {interview_id}, {email}: {error}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully processed {pending_interviews.count()} interviews "
                    f"({pending_interviews.count() * 2 - len(failed_emails)} emails sent, "
                    f"{len(failed_emails)} failed)"
                )
            )

        else:
            self.stdout.write(
                self.style.SUCCESS("\nDry run completed - no notifications were sent")
            )
            
            # what would have been sent
            for interview in pending_interviews:
                self.stdout.write(
                    f"Would send notifications for: "
                    f"{interview.interviewer.username} ({interview.interviewer.email}) <-> "
                    f"{interview.interviewee.username} ({interview.interviewee.email})"
                )