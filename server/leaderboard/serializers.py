from rest_framework import serializers
from .models import LeetcodeStats
from members.serializers import UsernameSerializer


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
