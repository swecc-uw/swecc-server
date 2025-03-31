from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.core.management.base import BaseCommand
from django.db import models
from members.models import User


class Command(BaseCommand):

    disallowed_fields = {
        "password",
        "linkedin",
        "github",
        "leetcode",
        "created",
        "id",
        "discord_id",
        "is_staff",
        "is_active",
        "date_joined",
    }
    allowed_types = {
        models.BigIntegerField.__name__,
        models.URLField.__name__,
        models.CharField.__name__,
        models.TextField.__name__,
    }

    def output_info(field_name):
        return "`" + str(field_name) + "`"

    help = f"Command to set a particular field (defaults to `username`) of a user to a given value. Disallowed fields include: {', '.join(map(output_info, disallowed_fields))}."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username", type=str, help="SWECC Interview Website Username"
        )
        parser.add_argument(
            "--field", type=str, help="Field to update", default="username"
        )
        parser.add_argument("--value", type=str, help="Value to set field to")

    def handle(self, *args, **options):
        username = options["username"]
        field = options["field"]
        value = options["value"]

        if field in self.disallowed_fields:
            self.stdout.write(
                self.style.ERROR(
                    f"Disallowed from modifying field {Command.output_info(field)}."
                )
            )
            return

        user_to_update = User.objects.filter(username=username).first()
        if user_to_update is None:
            self.stdout.write(self.style.ERROR(f"Username {username} was not found!"))
            return

        try:
            field_metadata = User._meta.get_field(field_name=field)
            field_type = field_metadata.get_internal_type()
        except FieldDoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"Field {Command.output_info(field)} does not exist on the User object."
                )
            )
            return

        if field_type not in self.allowed_types:
            self.stdout.write(
                self.style.ERROR(
                    f"Cannot write to type {Command.output_info(field_type)}."
                )
            )
            return

        try:
            if field_type == models.BigIntegerField.__name__:
                value = int(value)

            user_to_update.__setattr__(field, value)

            # Ensure integrity regarding fields and types to prevent type mismatches and other related issues
            user_to_update.full_clean()
            user_to_update.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated field {Command.output_info(field)} with value {Command.output_info(value)} for user {Command.output_info(username)}."
                )
            )
        except (ValidationError, ValueError) as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Exception while updating field {Command.output_info(field)} with value {Command.output_info(value)}: {e.message}."
                )
            )
            return
