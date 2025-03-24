from dataclasses import dataclass
from typing import Dict
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
    name = models.CharField(max_length=255, unique=True)
    level = models.CharField(
        max_length=64, choices=LEVEL_CHOICES, db_index=True, default="beginner"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Cohort"
        verbose_name_plural = "Cohorts"

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


@dataclass
class CohortStatsData:
    applications: int = 0
    online_assessments: int = 0
    interviews: int = 0
    offers: int = 0
    daily_checks: int = 0
    streak: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "applications": self.applications,
            "onlineAssessments": self.online_assessments,
            "interviews": self.interviews,
            "offers": self.offers,
            "dailyChecks": self.daily_checks,
            "streak": self.streak,
        }

    @classmethod
    def from_db_values(cls, values: Dict[str, int]) -> "CohortStatsData":
        return cls(
            applications=values.get("applications__sum", 0) or 0,
            online_assessments=values.get("onlineAssessments__sum", 0) or 0,
            interviews=values.get("interviews__sum", 0) or 0,
            offers=values.get("offers__sum", 0) or 0,
            daily_checks=values.get("dailyChecks__sum", 0) or 0,
            streak=values.get("streak__max", 0) or 0,
        )
