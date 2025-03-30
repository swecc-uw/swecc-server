from interview.models import Interview
from interview.serializers import InterviewMemberSerializer
from members.models import User
from members.serializers import UserSerializer
from questions.models import TechnicalQuestion
from questions.serializers import TechnicalQuestionSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    associated_id = serializers.SerializerMethodField()
    associated_object = serializers.SerializerMethodField()
    reporter = serializers.SerializerMethodField()
    associated_interview = serializers.PrimaryKeyRelatedField(
        queryset=Interview.objects.all(), required=False, allow_null=True
    )
    associated_question = serializers.PrimaryKeyRelatedField(
        queryset=TechnicalQuestion.objects.all(), required=False, allow_null=True
    )
    associated_member = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Report
        fields = [
            "report_id",
            "associated_interview",
            "associated_question",
            "associated_member",
            "associated_id",
            "associated_object",
            "type",
            "reason",
            "status",
            "updated",
            "created",
            "assignee",
            "admin_notes",
            "reporter",
        ]
        read_only_fields = ["report_id", "created", "updated"]

    def get_associated_id(self, obj):
        return obj.get_associated_id()

    def get_associated_object(self, obj):
        if obj.type == "interview" and obj.associated_interview:
            return InterviewMemberSerializer(obj.associated_interview).data
        elif obj.type == "question" and obj.associated_question:
            return TechnicalQuestionSerializer(obj.associated_question).data
        elif obj.type == "member" and obj.associated_member:
            return UserSerializer(obj.associated_member).data
        return None

    def get_reporter(self, obj):
        return UserSerializer(obj.reporter_user_id).data

    def validate(self, data):
        report_type = data.get("type")
        status = data.get("status")
        interview = data.get("associated_interview", None)
        question = data.get("associated_question", None)
        member = data.get("associated_member", None)

        #  only one object
        associated_objects = [
            obj for obj in [interview, question, member] if obj is not None
        ]
        if len(associated_objects) > 1:
            raise ValidationError(
                "Only one of associated_interview, associated_question, or associated_member should be provided"
            )

        if report_type not in [c[0] for c in Report.REPORT_TYPE_CHOICES]:
            raise ValidationError(
                f"Invalid report type: {report_type}, must be one of {Report.REPORT_TYPE_CHOICES}"
            )

        if status not in [c[0] for c in Report.STATUS_CHOICES]:
            raise ValidationError(
                f"Invalid status: {status}, must be one of {Report.STATUS_CHOICES}"
            )

        return data
