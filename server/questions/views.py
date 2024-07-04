from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import TechnicalQuestion, QuestionTopic, BehavioralQuestion
from .serializers import TechnicalQuestionSerializer, QuestionTopicSerializer, BehavioralQuestionSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter

class QuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    lookup_field = 'question_id'

    @extend_schema(
        parameters=[
            OpenApiParameter(name='type', description='Question type (technical or behavioral)', required=True, type=str)
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.kwargs.get('type') == 'technical':
            return TechnicalQuestionSerializer
        elif self.kwargs.get('type') == 'behavioral':
            return BehavioralQuestionSerializer
        return TechnicalQuestionSerializer  # TODO: replace with reasonable default

    def get_queryset(self):
        if self.kwargs.get('type') == 'technical':
            return TechnicalQuestion.objects.all()
        elif self.kwargs.get('type') == 'behavioral':
            return BehavioralQuestion.objects.all()
        return TechnicalQuestion.objects.none()  # TODO: replace with reasonable default

class QuestionCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='type', description='Question type (technical or behavioral)', required=True, type=str)
        ]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.kwargs.get('type') == 'technical':
            return TechnicalQuestionSerializer
        elif self.kwargs.get('type') == 'behavioral':
            return BehavioralQuestionSerializer
        return TechnicalQuestionSerializer  # TODO: replace with reasonable default

    def get_queryset(self):
        if self.kwargs.get('type') == 'technical':
            return TechnicalQuestion.objects.all()
        elif self.kwargs.get('type') == 'behavioral':
            return BehavioralQuestion.objects.all()
        return TechnicalQuestion.objects.none()  # TODO: replace with reasonable default

class QuestionListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='type', description='Question type (technical or behavioral)', required=True, type=str),
            OpenApiParameter(name='topic', description='Filter by topic name', required=False, type=str)
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.kwargs.get('type') == 'technical':
            return TechnicalQuestionSerializer
        elif self.kwargs.get('type') == 'behavioral':
            return BehavioralQuestionSerializer
        return TechnicalQuestionSerializer  # TODO: replace with reasonable default

    def get_queryset(self):
        if self.kwargs.get('type') == 'technical':
            queryset = TechnicalQuestion.objects.all()
        elif self.kwargs.get('type') == 'behavioral':
            queryset = BehavioralQuestion.objects.all()
        else:
            return TechnicalQuestion.objects.none()  # TODO: replace with reasonable default

        topic = self.request.query_params.get('topic', None)
        if topic is not None:
            queryset = queryset.filter(topic__name=topic)
        return queryset

class QuestionTopicListView(generics.ListCreateAPIView):
    queryset = QuestionTopic.objects.all()
    serializer_class = QuestionTopicSerializer
    permission_classes = [permissions.AllowAny]