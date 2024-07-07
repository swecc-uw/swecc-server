from rest_framework import serializers
from .models import InterviewPool, Interview, InterviewAvailability


class AvailabilitySerializer(serializers.Serializer):
    class Meta:
        model = InterviewAvailability
        fields = "__all__"


class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = "__all__"


class InterviewPoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewPool
        fields = "__all__"
