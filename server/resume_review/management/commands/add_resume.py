from django.core.management.base import BaseCommand, CommandParser
from resume_review.models import Resume
from members.models import User
from django.db import IntegrityError

class Command(BaseCommand):
    help = "Command to add resumes"

    def handle(self, *args, **options):
        feedback = options.get("feedback")
        username = options.get("username")
        file_name = options.get("file_name")
        file_size = options.get("file_size")

        if feedback is None or  username is None or file_name is None or file_size is None:
            self.stdout.write("Error processing parameters")
            return
        member = User.objects.filter(username = username).first()
        if member is None:
            self.stdout.write("User not found") 
            return
        try:
            resume = Resume.objects.create(member=member,feedback=feedback,file_name=file_name,file_size=file_size)
            self.stdout.write("Successfully created resume")
        except IntegrityError:
            self.stdout.write("Duplicate file name found")
        
        

        
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--feedback", type=str,help="The feedback on this particular resume")
        parser.add_argument("--username", type=str,help="The username associated with this particular resume")
        parser.add_argument("--file_name", type=str,help="The file name of this particular resume")
        parser.add_argument("--file_size",type=int,help="The file size of this particular resume")

