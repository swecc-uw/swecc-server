from cohort.models import Cohort
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from members.models import User


class AttendanceSession(models.Model):
    session_id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=20)  # only active session keys have to be unique
    title = models.CharField(max_length=100)
    expires = models.DateTimeField()
    attendees = models.ManyToManyField(User, related_name="attendance_sessions")

    class Meta:
        indexes = [models.Index(fields=["-expires"])]

    def clean(self):
        # Expires must be in UTC
        if self.expires and self.expires.tzinfo != timezone.utc:
            self.expires = self.expires.astimezone(timezone.utc)

        # Key must be unique for active sessions
        if not self.pk:
            active_session = AttendanceSession.objects.filter(
                key=self.key, expires__gt=timezone.now()
            ).exists()
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

    class Meta:
        unique_together = ["member", "channel_id"]

    def __str__(self):
        return f"{self.member_id.username} - {self.channel_id} - {self.message_count}"


# Derived data
# Any time we implement a view that modifies the number of attendance sessions tied to a particular user, we must update this model accordingly.
class AttendanceSessionStats(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    sessions_attended = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.member.username}: {self.sessions_attended}"


class CohortStats(models.Model):
    member = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cohort_member_stats"
    )
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    applications = models.IntegerField(default=0)
    onlineAssessments = models.IntegerField(default=0)
    interviews = models.IntegerField(default=0)
    offers = models.IntegerField(default=0)
    dailyChecks = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    streak = models.IntegerField(default=0)
