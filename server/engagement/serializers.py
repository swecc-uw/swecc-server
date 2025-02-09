from rest_framework import serializers
from .models import AttendanceSession, AttendanceSessionStats, CohortStats
from members.models import User
from members.serializers import UsernameSerializer, UserSerializer
from cohort.serializers import CohortSerializer


class AttendeeSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username"]


class AttendanceSessionSerializer(serializers.ModelSerializer):

    attendees = AttendeeSerializer(many=True, read_only=True)

    class Meta:
        model = AttendanceSession
        fields = "__all__"


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id"]


class AttendanceStatsSerializer(serializers.ModelSerializer):
    member = UsernameSerializer(read_only=True)
    rank = serializers.IntegerField()

    class Meta:
        model = AttendanceSessionStats
        fields = "__all__"


class CohortStatsSerializer(serializers.ModelSerializer):
    member = UserSerializer(read_only=True)
    cohort = CohortSerializer(read_only=True)

    class Meta:
        model = CohortStats
        fields = [
            "member",
            "cohort",
            "applications",
            "onlineAssessments",
            "interviews",
            "offers",
            "dailyChecks",
        ]


class CohortStatsLeaderboardSerializer(serializers.ModelSerializer):
    member = UsernameSerializer
    rank = serializers.IntegerField()

    class Meta:
        model = CohortStats
        fields = "__all__"
