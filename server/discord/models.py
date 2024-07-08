from django.db import models
import uuid

class AuthKey(models.Model):
    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    discord_id = models.CharField(max_length=50, unique=False, null=True, blank=True)
    discord_username = models.CharField(max_length=50, null=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.key)