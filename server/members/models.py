from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models


def validate_social_field(value):
    if value is None:
        return
    required_keys = {"username", "isPrivate"}
    if not isinstance(value, dict):
        raise ValidationError("Field must be a dictionary.")
    if set(value.keys()) != required_keys:
        raise ValidationError(
            f"Field must contain exactly the following keys: {required_keys}"
        )
    if not isinstance(value["username"], str):
        raise ValidationError('The "username" field must be a string.')
    if not isinstance(value["isPrivate"], bool):
        raise ValidationError('The "isPrivate" field must be a boolean.')


class CustomUserManager(UserManager):
    def get_by_natural_key(self, username):
        case_insensitive_username_field = "{}__iexact".format(self.model.USERNAME_FIELD)
        return self.get(**{case_insensitive_username_field: username})


class User(AbstractUser):
    first_name = models.CharField(blank=True, max_length=20)
    last_name = models.CharField(blank=True, max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    preview = models.TextField(blank=True, null=True)
    major = models.CharField(max_length=100, blank=True, null=True)
    grad_date = models.DateField(blank=True, null=True)
    discord_username = models.CharField(max_length=100)
    linkedin = models.JSONField(
        blank=True, null=True, validators=[validate_social_field]
    )
    github = models.JSONField(blank=True, null=True, validators=[validate_social_field])
    leetcode = models.JSONField(
        blank=True, null=True, validators=[validate_social_field]
    )
    resume_url = models.URLField(blank=True, null=True)
    local = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    discord_id = models.BigIntegerField(null=True, blank=True)
    profile_picture_url = models.URLField(blank=True, null=True)
    school_email = models.EmailField(blank=True, null=True, unique=True)

    objects = CustomUserManager()

    class Meta:
        permissions = (
            ("is_verified", "Users discord is verified"),
            ("is_admin", "User is an admin"),
        )

        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["first_name"]),
            models.Index(fields=["last_name"]),
        ]
