from rest_framework import serializers
from members.models import User


class BaseDirectoryMemberSerializer(serializers.ModelSerializer):
    linkedin = serializers.SerializerMethodField()
    github = serializers.SerializerMethodField()
    leetcode = serializers.SerializerMethodField()

    def get_social_field(self, obj, field_name):
        field = getattr(obj, field_name)
        if isinstance(field, dict) and not field.get("isPrivate", True):
            return {k: v for k, v in field.items() if k != "isPrivate"}
        return None

    def get_linkedin(self, obj):
        return self.get_social_field(obj, "linkedin")

    def get_github(self, obj):
        return self.get_social_field(obj, "github")

    def get_leetcode(self, obj):
        return self.get_social_field(obj, "leetcode")

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # remove empty fields
        fields_to_remove = set()
        for field in representation:
            if representation.get(field) in [None, ""]:
                fields_to_remove.add(field)

        for field in fields_to_remove:
            representation.pop(field)

        return representation


class RegularDirectoryMemberSerializer(BaseDirectoryMemberSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "discord_username",
            "first_name",
            "last_name",
            "major",
            "grad_date",
            "linkedin",
            "github",
            "leetcode",
        ]


class AdminDirectoryMemberSerializer(BaseDirectoryMemberSerializer):
    class Meta:
        model = User
        exclude = ("password",)
