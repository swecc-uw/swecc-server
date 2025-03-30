from rest_framework import serializers
from .models import TechnicalQuestion, QuestionTopic, BehavioralQuestion
from members.serializers import UsernameSerializer


class QuestionTopicSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = QuestionTopic
        fields = "__all__"
        extra_kwargs = {"created_by": {"read_only": True}}


class TechnicalQuestionSerializer(serializers.ModelSerializer):
    topic = serializers.PrimaryKeyRelatedField(
        queryset=QuestionTopic.objects.all(), write_only=False
    )

    created_by = serializers.CharField(source="created_by.username", read_only=True)
    approved_by = serializers.CharField(
        source="approved_by.username", read_only=True, allow_null=True
    )

    class Meta:
        model = TechnicalQuestion
        fields = "__all__"
        extra_kwargs = {
            "created_by": {"read_only": True},
            "approved_by": {"read_only": True},
            "question_id": {"read_only": True},
            "created": {"read_only": True},
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if isinstance(instance.topic, QuestionTopic):
            topic_serializer = QuestionTopicSerializer(instance.topic)
            representation["topic"] = topic_serializer.data

        return representation


class BehavioralQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehavioralQuestion
        fields = "__all__"
        extra_kwargs = {
            "created_by": {"read_only": True},
            "approved_by": {"read_only": True},
        }


class UpdateQueueSerializer(serializers.Serializer):
    question_queue = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=True
    )

    def validate(self, data):
        """
        Extract just the question_queue list from the validated data
        """
        return data["question_queue"]
