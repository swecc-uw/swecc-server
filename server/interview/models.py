from django.db import models
from django.core.exceptions import ValidationError
import uuid

def default_availability():
    return [[False for _ in range(48)] for _ in range(7)]

def validate_availability(value):
    if not isinstance(value, list) or len(value) != 7:
        raise ValidationError("Availability must be a list of 7 days.")
    for day in value:
        if not isinstance(day, list) or len(day) != 48:
            raise ValidationError("Each day must be a list of 48 time slots.")
        if not all(isinstance(slot, bool) for slot in day):
            raise ValidationError("Each time slot must be a boolean value.")

# Create your models here.
class InterviewAvailability(models.Model):
    member = models.OneToOneField(
        'members.User',
        on_delete=models.CASCADE,
        primary_key=True
    )
    interview_availability_slots = models.JSONField(
        default=default_availability,
        validators=[validate_availability]
    )
    mentor_availability_slots = models.JSONField(
        default=default_availability,
        validators=[validate_availability]
    )

    def set_interview_availability(self, availability):
        validate_availability(availability)
        self.interview_availability_slots = availability

    def set_mentor_availability(self, availability):
        validate_availability(availability)
        self.mentor_availability_slots = availability

    def __str__(self):
        return f"Availability for {self.member}"


class InterviewPool(models.Model):
    member = models.OneToOneField(
        'members.User',
        on_delete=models.CASCADE,
        primary_key=True
    )

    def __str__(self):
        return f"Interview Pool: {self.member}"


class Interview(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('inactive_unconfirmed', 'Inactive Unconfirmed'),
        ('inactive_completed', 'Inactive Completed'),
        ('inactive_incomplete', 'Inactive Incomplete')
    ]

    interview_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interviewer = models.ForeignKey('members.User', on_delete=models.CASCADE, related_name='interviews_as_interviewer')
    technical_questions = models.ManyToManyField('questions.TechnicalQuestion')
    behavioral_questions = models.ManyToManyField('questions.BehavioralQuestion')
    interviewee = models.ForeignKey('members.User', on_delete=models.CASCADE, related_name='interviews_as_interviewee')
    status = models.CharField(max_length=64, choices=STATUS_CHOICES, default='pending')
    proposed_time = models.DateTimeField(null=True, blank=True)
    proposed_by = models.ForeignKey('members.User', on_delete=models.SET_NULL, null=True, related_name='proposed_interviews')
    committed_time = models.DateTimeField(null=True, blank=True)
    date_effective = models.DateTimeField()
    date_completed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Interview {self.interview_id}: {self.interviewer} - {self.interviewee}"
