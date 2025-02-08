from django.db import models


class Cohort(models.Model):
    LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    members = models.ManyToManyField(
        "members.User", related_name="cohorts", blank=True, db_table="cohort_members"
    )
    name = models.CharField(max_length=255)
    level = models.CharField(
        max_length=64, choices=LEVEL_CHOICES, db_index=True, default="beginner"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Cohort"
        verbose_name_plural = "Cohorts"

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"
