from rest_framework import serializers

from members.models import User
from .models import Report
from members.serializers import UserSerializer
from interview.serializers import InterviewSerializer
from questions.serializers import TechnicalQuestionSerializer

class ReportSerializer(serializers.ModelSerializer):
    associated_id = serializers.SerializerMethodField()
    associated_object = serializers.SerializerMethodField()
    reporter_user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Report
        fields = [
            'report_id',
            'associated_id',
            'associated_object',
            'type',
            'reporter_user_id',
            'reason',
            'status',
            'updated',
            'created',
            'admin_id',
            'admin_notes'
        ]
        read_only_fields = ['report_id', 'created', 'updated']

    def get_associated_id(self, obj):
        return obj.get_associated_id()

    def get_associated_object(self, obj):
        if obj.type == 'interview' and obj.associated_interview:
            return InterviewSerializer(obj.associated_interview).data
        elif obj.type == 'question' and obj.associated_question:
            return TechnicalQuestionSerializer(obj.associated_question).data
        elif obj.type == 'member' and obj.associated_member:
            return UserSerializer(obj.associated_member).data
        return None