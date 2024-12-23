from rest_framework import serializers

from questions.serializers import BehavioralQuestionSerializer, TechnicalQuestionSerializer
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

class InterviewAndQuestionSerializer(serializers.ModelSerializer):
    technical_questions = TechnicalQuestionSerializer(many=True, read_only=True, source='technical_questions.all')
    behavioral_questions = BehavioralQuestionSerializer(many=True, read_only=True, source='behavioral_questions.all')

    class Meta:
        model = Interview
        fields = [
            'interview_id',
            'interviewer',
            'interviewee',
            'technical_questions',
            'behavioral_questions',
            'status',
            'date_effective',
            'date_completed',
        ]