from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from members.models import User


class Announcement(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    content = models.TextField()

    def __str__(self):
        return f"{self.title}"

