from rest_framework import serializers

from members.serializers import UserSerializer
from .models import Cohort, CohortStats


class CohortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = ["id", "name", "members"]


class CohortHydratedSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Cohort
        fields = ["id", "name", "members"]


class CohortStatsSerializer(serializers.ModelField):
    member = UserSerializer(read_only=True)
    cohort = CohortSerializer

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
