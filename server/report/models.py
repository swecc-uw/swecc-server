from django.db import models
import uuid

# Create your models here.
class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('interview', 'Interview'),
        ('question', 'Question'),
        # Add other types as needed
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('resolving', 'Resolving'),
        ('completed', 'Completed'),
    ]

    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    associated_id = models.ForeignKey('interview.Interview', null=True, blank=True, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    reporter_member_id = models.UUIDField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    admin_id = models.UUIDField(null=True, blank=True)  # Nullable admin reference
    admin_notes = models.TextField(null=True, blank=True)  # Optional admin notes
