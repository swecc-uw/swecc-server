from rest_framework import serializers
from .models import TechnicalQuestion, QuestionTopic, BehavioralQuestion

class TechnicalQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalQuestion
        fields = '__all__'
        extra_kwargs = {"created_by": {"read_only": True}, "approved_by": {"read_only": True} }

class QuestionTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionTopic
        fields = '__all__'
        extra_kwargs = {"created_by": {"read_only": True}}

class BehavioralQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehavioralQuestion
        fields = '__all__'
        extra_kwargs = {"created_by": {"read_only": True}, "approved_by": {"read_only": True} }