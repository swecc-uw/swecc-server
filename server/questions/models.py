from django.db import models
from members.models import User
import uuid


class QuestionTopic(models.Model):
    topic_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, related_name="topic_created_by", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class TechnicalQuestion(models.Model):
    title = models.CharField(max_length=100)
    question_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, related_name="technical_questions_created", on_delete=models.CASCADE
    )
    approved_by = models.ForeignKey(
        User,
        related_name="technical_questions_approved",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    last_assigned = models.DateField(blank=True, null=True)
    topic = models.ForeignKey(QuestionTopic, on_delete=models.CASCADE)
    prompt = models.TextField()
    solution = models.TextField()
    follow_ups = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)


class BehavioralQuestion(models.Model):
    question_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, related_name="behavioral_questions_created", on_delete=models.CASCADE
    )
    approved_by = models.ForeignKey(
        User,
        related_name="behavioral_questions_approved",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    last_assigned = models.DateField(blank=True, null=True)
    prompt = models.TextField()
    solution = models.TextField()
    follow_ups = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)


class TechnicalQuestionQueue(models.Model):
    question = models.OneToOneField(
        TechnicalQuestion, on_delete=models.CASCADE, related_name="queue_position"
    )
    position = models.IntegerField()
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return f"{self.question.title} - Position {self.position}"


class BehavioralQuestionQueue(models.Model):
    question = models.OneToOneField(
        BehavioralQuestion, on_delete=models.CASCADE, related_name="queue_position"
    )
    position = models.IntegerField()
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return f"{self.question.prompt[:50]} - Position {self.position}"
