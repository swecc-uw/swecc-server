from rest_framework import generics, permissions

from .models import TechnicalQuestion, QuestionTopic, BehavioralQuestion
from .serializers import TechnicalQuestionSerializer, QuestionTopicSerializer, BehavioralQuestionSerializer
from custom_auth.permissions import IsAdmin
import logging

logger = logging.getLogger(__name__)
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
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.kwargs['type'] == 'technical':
            return TechnicalQuestionSerializer
        elif self.kwargs['type'] == 'behavioral':
            return BehavioralQuestionSerializer
    
    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(created_by=self.request.user)
        else:
            logger.error('Error creating question: %s', serializer.errors)

    def get_queryset(self):
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

class QuestionTopicListCreateView(generics.ListCreateAPIView):
    queryset = QuestionTopic.objects.all()
    serializer_class = QuestionTopicSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [IsAdmin]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class QuestionTopicUpdateView(generics.RetrieveUpdateAPIView):
    queryset = QuestionTopic.objects.all()
    serializer_class = QuestionTopicSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'topic_id'