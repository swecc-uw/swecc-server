from django.db import models
from members.models import User


class Resume(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback = models.TextField()
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
