import time
from urllib import request
from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from members.serializers import User

from .models import TechnicalQuestion, QuestionTopic, BehavioralQuestion
from .serializers import TechnicalQuestionSerializer, QuestionTopicSerializer, BehavioralQuestionSerializer

class QuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'question_id'

    def get_serializer_class(self):
        if self.kwargs['type'] == 'technical':
            return TechnicalQuestionSerializer
        elif self.kwargs['type'] == 'behavioral':
            return BehavioralQuestionSerializer

    def get_queryset(self):
        if self.kwargs['type'] == 'technical':
            return TechnicalQuestion.objects.all()
        elif self.kwargs['type'] == 'behavioral':
            return BehavioralQuestion.objects.all()

class QuestionCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if not self.request.user.is_authenticated:
            self.request.user = User.objects.first()
        if self.kwargs['type'] == 'technical':
            return TechnicalQuestionSerializer
        elif self.kwargs['type'] == 'behavioral':
            return BehavioralQuestionSerializer
        elif self.kwargs['type'] == 'topic':
            return QuestionTopicSerializer
    
    def perform_create(self, serializer):
        if serializer.is_valid():
            if self.kwargs['type'] != 'topic':
                # TODO: if a topic is not provided, create a new one
                serializer.save(created_by=self.request.user)
            elif self.kwargs['type'] == 'topic':
                serializer.save()
        else:
            print(serializer.errors)

    def get_queryset(self):
        user = self.request.user
        if self.kwargs['type'] == 'technical':
            return TechnicalQuestion.objects.all()
        elif self.kwargs['type'] == 'behavioral':
            return BehavioralQuestion.objects.all()

class QuestionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.kwargs['type'] == 'technical':
            return TechnicalQuestionSerializer
        elif self.kwargs['type'] == 'behavioral':
            return BehavioralQuestionSerializer

    def get_queryset(self):
        if self.kwargs['type'] == 'technical':
            queryset = TechnicalQuestion.objects.all()
        elif self.kwargs['type'] == 'behavioral':
            queryset = BehavioralQuestion.objects.all()

        topic = self.request.query_params.get('topic', None)
        if topic is not None:
            queryset = queryset.filter(topic__name=topic)
        return queryset

class QuestionTopicListView(generics.ListCreateAPIView):
    queryset = QuestionTopic.objects.all()
    serializer_class = QuestionTopicSerializer
    permission_classes = [permissions.IsAuthenticated]