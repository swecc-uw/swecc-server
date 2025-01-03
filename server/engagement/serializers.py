from rest_framework import serializers
from .models import AttendanceSession, AttendanceSessionStats
from members.models import User
from members.serializers import UsernameSerializer


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

    class Meta:
        model = AttendanceSessionStats
        fields = "__all__"
