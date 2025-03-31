import uuid

from django.db import models
from interview.models import Interview
from members.models import User
from questions.models import TechnicalQuestion


class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ("interview", "Interview"),
        ("question", "Question"),
        ("member", "Member"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("resolving", "Resolving"),
        ("completed", "Completed"),
    ]

    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    associated_interview = models.ForeignKey(
        Interview, null=True, blank=True, on_delete=models.CASCADE
    )
    associated_question = models.ForeignKey(
        TechnicalQuestion, null=True, blank=True, on_delete=models.CASCADE
    )
    associated_member = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="reported_user",
    )

    type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    reporter_user_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reporter"
    )
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    admin_notes = models.TextField(null=True, blank=True)
    assignee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="assigned_report",
    )

    def get_associated_id(self):
        if self.type == "interview":
            return (
                str(self.associated_interview.interview_id)
                if self.associated_interview
                else None
            )
        elif self.type == "question":
            return (
                str(self.associated_question.question_id)
                if self.associated_question
                else None
            )
        elif self.type == "member":
            return str(self.associated_member.id) if self.associated_member else None
        return None
