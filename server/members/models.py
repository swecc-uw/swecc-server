from django.db import models
import uuid

class Member(models.Model):
    member_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(max_length=254, unique=True)
    role = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    preview = models.TextField(blank=True, null=True)
    major = models.CharField(max_length=100, blank=True, null=True)
    grad_date = models.DateField(blank=True, null=True)
    discord_username = models.CharField(max_length=100)
    linkedin_username = models.CharField(max_length=100, blank=True, null=True)
    github_username = models.CharField(max_length=100, blank=True, null=True)
    leetcode_username = models.CharField(max_length=100, blank=True, null=True)
    resume_url = models.URLField(blank=True, null=True)
    local = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    discord_id = models.IntegerField()