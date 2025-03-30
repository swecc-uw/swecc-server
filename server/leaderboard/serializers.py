from members.serializers import UsernameSerializer
from rest_framework import serializers

from .models import (
    GitHubStats,
    InternshipApplicationStats,
    LeetcodeStats,
    NewGradApplicationStats,
)


class LeetcodeStatsSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = LeetcodeStats
        fields = [
            "user",
            "total_solved",
            "easy_solved",
            "medium_solved",
            "hard_solved",
            "last_updated",
        ]

    def get_user(self, obj):
        return {"username": obj.user.leetcode["username"]}


class GitHubStatsSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = GitHubStats
        fields = [
            "user",
            "total_prs",
            "total_commits",
            "followers",
            "last_updated",
        ]

    def get_user(self, obj):
        return {"username": obj.user.github["username"]}


class InternshipApplicationStatsSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = InternshipApplicationStats
        fields = ["user", "applied", "last_updated"]

    def get_user(self, obj):
        return {"username": obj.user.username}


class NewGradApplicationStatsSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = NewGradApplicationStats
        fields = ["user", "applied", "last_updated"]

    def get_user(self, obj):
        return {"username": obj.user.username}
