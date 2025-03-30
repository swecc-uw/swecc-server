from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import User
from django.contrib.auth.models import Group


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("name",)


class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True)

    class Meta:
        model = User
        exclude = ["password"]


class UsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]
