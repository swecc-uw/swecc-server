from rest_framework import serializers

from members.serializers import UserSerializer
from .models import Cohort


class CohortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = ["id", "name", "members", "level"]


class CohortNoMembersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = ["id", "name", "level"]


class CohortHydratedSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Cohort
        fields = ["id", "name", "members", "level"]


class CohortHydratedPublicSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Cohort
        fields = ["id", "name", "members"]
