from members.models import User
from django.core.management.base import BaseCommand
from django.db import models
from django.core.exceptions import ValidationError, FieldDoesNotExist
from django.contrib.auth.models import AbstractUser


class Command(BaseCommand):
    help = "Command to set a particular field of a user to a given value"

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

    allowed_fields = set(User._meta.get_fields() + AbstractUser._meta.get_fields())

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
                self.style.ERROR(f"Disallowed from modifying field '{field}'")
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
                self.style.ERROR(f"Field '{field}' does not exist on the User object.")
            )
            return

        if not field_type in self.allowed_types:
            self.stdout.write(self.style.ERROR(f"Cannot write to type '{field_type}'"))
            return

        try:
            if field_type == models.BigIntegerField.__name__:
                value = int(value)

            user_to_update.__setattr__(field, value)

            user_to_update.full_clean()
            user_to_update.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated field '{field}' with value '{value}' for user '{username}'"
                )
            )
        except (ValidationError, ValueError) as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Exception while updating field '{field}' with value '{value}': {e.message}"
                )
            )
            return
