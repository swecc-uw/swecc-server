from django.db import models
from django.core.exceptions import ValidationError
import uuid

def validate_social_field(value):
    if value is None:
        return
    required_keys = {'username', 'isPrivate'}
    if not isinstance(value, dict):
        raise ValidationError('Field must be a dictionary.')
    if set(value.keys()) != required_keys:
        raise ValidationError(f'Field must contain exactly the following keys: {required_keys}')
    if not isinstance(value['username'], str):
        raise ValidationError('The "username" field must be a string.')
    if not isinstance(value['isPrivate'], bool):
        raise ValidationError('The "isPrivate" field must be a boolean.')

class Member(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(max_length=254, unique=True)
    role = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    preview = models.TextField(blank=True, null=True)
    major = models.CharField(max_length=100, blank=True, null=True)
    grad_date = models.DateField(blank=True, null=True)
    discord_username = models.CharField(max_length=100)
    linkedin = models.JSONField(blank=True, null=True, validators=[validate_social_field])
    github = models.JSONField(blank=True, null=True, validators=[validate_social_field])
    leetcode = models.JSONField(blank=True, null=True, validators=[validate_social_field])
    resume_url = models.URLField(blank=True, null=True)
    local = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    discord_id = models.IntegerField()