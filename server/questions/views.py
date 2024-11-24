from rest_framework import generics, permissions

from .models import (
    BehavioralQuestionQueue,
    TechnicalQuestion,
    QuestionTopic,
    BehavioralQuestion,
    TechnicalQuestionQueue,
)
from .serializers import (
    TechnicalQuestionSerializer,
    QuestionTopicSerializer,
    BehavioralQuestionSerializer,
    UpdateQueueSerializer,
)
from custom_auth.permissions import IsAdmin, IsVerified
import logging
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

logger = logging.getLogger(__name__)


class QuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsVerified]
    lookup_field = "question_id"

    def get_serializer_class(self):
        if self.kwargs["type"] == "technical":
            return TechnicalQuestionSerializer
        elif self.kwargs["type"] == "behavioral":
            return BehavioralQuestionSerializer

    def get_queryset(self):
        if self.kwargs["type"] == "technical":
            return TechnicalQuestion.objects.all()
        elif self.kwargs["type"] == "behavioral":
            return BehavioralQuestion.objects.all()


class QuestionCreateView(generics.CreateAPIView):
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.kwargs["type"] == "technical":
            return TechnicalQuestionSerializer
        elif self.kwargs["type"] == "behavioral":
            return BehavioralQuestionSerializer

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(created_by=self.request.user)
        else:
            logger.error("Error creating question: %s", serializer.errors)

    def get_queryset(self):
        if self.kwargs["type"] == "technical":
            return TechnicalQuestion.objects.all()
        elif self.kwargs["type"] == "behavioral":
            return BehavioralQuestion.objects.all()


class QuestionListView(generics.ListAPIView):
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.kwargs["type"] == "technical":
            return TechnicalQuestionSerializer
        elif self.kwargs["type"] == "behavioral":
            return BehavioralQuestionSerializer

    def get_queryset(self):
        if self.kwargs["type"] == "technical":
            queryset = TechnicalQuestion.objects.all()
        elif self.kwargs["type"] == "behavioral":
            queryset = BehavioralQuestion.objects.all()

        topic = self.request.query_params.get("topic", None)
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
            self.permission_classes = [permissions.IsAuthenticated, IsVerified]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class QuestionTopicUpdateView(generics.RetrieveUpdateAPIView):
    queryset = QuestionTopic.objects.all()
    serializer_class = QuestionTopicSerializer
    permission_classes = [IsAdmin]
    lookup_field = "topic_id"

class QuestionQueueUpdateView(generics.GenericAPIView):
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.kwargs["type"] == "technical" or self.kwargs["type"] == "behavioral":
            return UpdateQueueSerializer
        else:
            raise RuntimeError("Invalid question type")

    def get_queue_model(self):
        if self.kwargs["type"] == "technical":
            return TechnicalQuestionQueue
        elif self.kwargs["type"] == "behavioral":
            return BehavioralQuestionQueue
        else:
            raise RuntimeError("Invalid question type")

    def get_question_model(self):
        if self.kwargs["type"] == "technical":
            return TechnicalQuestion
        elif self.kwargs["type"] == "behavioral":
            return BehavioralQuestion
        else:
            raise RuntimeError("Invalid question type")

    def get(self, request, *args, **kwargs):
        try:
            QueueModel = self.get_queue_model()
            queued_questions = QueueModel.objects.order_by("position").values_list(
                "question__question_id", flat=True
            )

            return Response({"question_queue": [str(id) for id in queued_questions]})

        except Exception as e:
            logger.error("Error retrieving question queue: %s", str(e))
            return Response(
                {"error": "Failed to retrieve queue"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error("Invalid queue update data: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question_ids = serializer.validated_data
        logger.info("Updating queue with questions: %s", question_ids)
        QueueModel = self.get_queue_model()
        QuestionModel = self.get_question_model()

        try:
            with transaction.atomic():
                # clear existing queue
                QueueModel.objects.all().delete()

                # verify all questions exist before creating queue
                questions = []
                for question_id in question_ids:
                    try:
                        question = QuestionModel.objects.get(question_id=question_id)
                        questions.append(question)
                    except QuestionModel.DoesNotExist:
                        logger.error(
                            "Question not found during queue update: %s", question_id
                        )
                        return Response(
                            {"error": f"Question with ID {question_id} does not exist"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                # create new queue entries
                queue_entries = [
                    QueueModel(question=question, position=position)
                    for position, question in enumerate(questions)
                ]

                QueueModel.objects.bulk_create(queue_entries)

            return Response({"message": "Queue updated successfully"})

        except Exception as e:
            logger.error("Error updating question queue: %s", str(e))
            return Response(
                {"error": "Failed to update queue"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
