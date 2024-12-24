from django.utils import timezone
from django.db import models
from members.models import User


class LeetcodeStats(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="leetcode_stats"
    )
    total_solved = models.IntegerField(default=0)
    easy_solved = models.IntegerField(default=0)
    medium_solved = models.IntegerField(default=0)
    hard_solved = models.IntegerField(default=0)
    last_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-total_solved", "-hard_solved", "-medium_solved"]
        verbose_name_plural = "Leetcode Stats"

    def __str__(self):
        return f"{self.user.username}'s Leetcode Stats"


class GitHubStats(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="github_stats"
    )
    total_prs = models.IntegerField(default=0)
    total_commits = models.IntegerField(default=0)
    followers = models.IntegerField(default=0)
    last_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-total_commits", "-total_prs"]
        verbose_name_plural = "GitHub Stats"

    def __str__(self):
        return f"{self.user.username}'s GitHub Stats"


class InternshipApplicationStats(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="internship_stats"
    )
    applied = models.IntegerField(default=0)

    class Meta:
        ordering = ["-applied"]
        verbose_name_plural = "Internship Application Stats"

    def __str__(self):
        return f"{self.user.username}'s Internship Application Stats"

class NewGradApplicationStats(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="new_grad_stats"
    )
    applied = models.IntegerField(default=0)

    class Meta:
        ordering = ["-applied"]
        verbose_name_plural = "New Grad Application Stats"

    def __str__(self):
        return f"{self.user.username}'s New Grad Application Stats"

