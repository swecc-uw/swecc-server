from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from members.models import User

class AttendanceSession(models.Model):
    session_id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=20) # only active session keys have to be unique
    title = models.CharField(max_length=100)
    expires = models.DateTimeField()
    attendees = models.ManyToManyField(User, related_name='attendance_sessions')

    class Meta:
        indexes = [models.Index(fields=['-expires'])]
    
    def clean(self):
        # Expires must be in UTC
        if self.expires and self.expires.tzinfo != timezone.utc:
            self.expires = self.expires.astimezone(timezone.utc)

        # Key must be unique for active sessions
        if not self.pk:
            active_session = AttendanceSession.objects.filter(key=self.key, expires__gt=timezone.now()).exists()
            if active_session:
                raise ValidationError("Key already exists for an active session")

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def is_active(self):
        """Returns true if the session is still active"""
        from django.utils.timezone import now
        return now() < self.expires

    def __str__(self):
        return f"{self.title} - {self.key} - {self.expires}"

class DiscordMessageStats(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    channel_id = models.CharField(max_length=100)
    message_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.member_id.username} - {self.channel_id} - {self.message_count}"
