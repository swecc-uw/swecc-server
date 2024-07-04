from django.db import models
from django.contrib.auth.models import User
import uuid

class QuestionTopic(models.Model):
    topic_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class TechnicalQuestion(models.Model):
    question_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='technical_questions_created', on_delete=models.CASCADE)
    approved_by = models.ForeignKey(User, related_name='technical_questions_approved', on_delete=models.SET_NULL, null=True, blank=True)
    last_assigned = models.DateField(blank=True, null=True)
    topic = models.ForeignKey(QuestionTopic, on_delete=models.CASCADE)
    prompt = models.TextField()
    solution = models.TextField()
    follow_ups = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    

class BehavioralQuestion(models.Model):
    question_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='behavioral_questions_created', on_delete=models.CASCADE)
    approved_by = models.ForeignKey(User, related_name='behavioral_questions_approved', on_delete=models.SET_NULL, null=True, blank=True)
    last_assigned = models.DateField(blank=True, null=True)
    prompt = models.TextField()
    solution = models.TextField() 
    follow_ups = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)