from django.db import models
from django.db.models import Q, UniqueConstraint
from members.models import User


class ReferralDetails(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("DENIED", "Denied"),
    )
    id = models.AutoField(primary_key=True)
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    active_until = models.DateField(null=True, blank=True)
    company = models.CharField(max_length=255)
    details = models.TextField(null=True, blank=True)
    expectations = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "member"]),
            models.Index(fields=["active_until"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["member"],
                condition=Q(status="PENDING"),
                name="unique_pending_referral_per_member",
            )
        ]

    def __str__(self):
        return f"{self.member.username} - {self.company} ({self.status})"


class ReferralDocument(models.Model):
    id = models.AutoField(primary_key=True)
    referral = models.ForeignKey(
        ReferralDetails, on_delete=models.CASCADE, related_name="documents"
    )
    file_path = models.CharField(
        max_length=255
    )  # format: referrals/{referral_id}/{document_id}.pdf
    uploaded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document for {self.referral.member.username} referral"
