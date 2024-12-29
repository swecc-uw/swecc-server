from django.db import models
from members.models import User

class AttendanceSession(models.Model):
    session_id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=10) # only active session keys have to be unique
    title = models.CharField(max_length=100)
    expires = models.DateTimeField()
    attendees = models.ManyToManyField(User, related_name='attendance_sessions')

    class Meta:
        indexes = [models.Index(fields=['-expires'])]

    def is_active(self):
        """Returns true if the session is still active"""
        from django.utils.timezone import now
        return now() < self.expires

    def __str__(self):
        return f"{self.title} - {self.key}"

class DiscordMessageStats(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    channel_id = models.CharField(max_length=100)
    message_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.member_id.username} - {self.channel_id} - {self.message_count}"
