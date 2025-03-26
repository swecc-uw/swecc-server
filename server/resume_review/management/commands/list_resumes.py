from resume_review.models import Resume
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Command to print out all resumes"

    def handle(self, *args, **options):
        pp = (
            lambda arg: f"ID: {arg['id']}, Feedback: {arg['feedback']}, File Info: {arg['file_name']}-{arg['file_size']}"
        )

        for resume in Resume.objects.all().values(
            "id", "feedback", "file_size", "file_name"
        ):
            self.stdout.write(self.style.SUCCESS(pp(resume)))
