from rest_framework import serializers
from .models import AttendanceSession
from members.models import User


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
