from rest_framework import serializers

from .models import ReferralDetails, ReferralDocument


class ReferralDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralDocument
        fields = ["id", "file_path", "uploaded", "created_at"]
        read_only_fields = ["id", "file_path", "uploaded", "created_at"]


class BaseReferralDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralDetails
        fields = [
            "id",
            "status",
            "active_until",
            "company",
            "expectations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ReferralProgramMemberSerializer(BaseReferralDetailsSerializer):
    member_username = serializers.ReadOnlyField(source="member.username")

    class Meta(BaseReferralDetailsSerializer.Meta):
        fields = BaseReferralDetailsSerializer.Meta.fields + ["member_username"]
        read_only_fields = BaseReferralDetailsSerializer.Meta.read_only_fields + [
            "status"
        ]


class AdminReferralDetailsSerializer(BaseReferralDetailsSerializer):
    member_username = serializers.ReadOnlyField(source="member.username")
    member_id = serializers.ReadOnlyField(source="member.id")
    documents = ReferralDocumentSerializer(many=True, read_only=True)

    class Meta(BaseReferralDetailsSerializer.Meta):
        fields = BaseReferralDetailsSerializer.Meta.fields + [
            "details",
            "member_username",
            "member_id",
            "documents",
        ]


class CreateReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralDetails
        fields = ["company", "details", "expectations"]
