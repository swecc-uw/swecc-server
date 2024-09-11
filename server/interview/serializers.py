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
    technical_question = TechnicalQuestionSerializer(read_only=True)
    behavioral_questions = BehavioralQuestionSerializer(many=True, read_only=True, source='behavioral_questions.all')

    class Meta:
        model = Interview
        fields = [
            'interview_id',
            'interviewer',
            'interviewee',
            'technical_question',
            'behavioral_questions',
            'status',
            'date_effective',
            'date_completed',
        ]