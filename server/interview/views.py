from email.policy import default
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .algorithm import CommonAvailabilityStableMatching
from .models import Interview
from .serializers import InterviewSerializer
from .models import InterviewAvailability, InterviewPool, Interview
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ValidationError
from rest_framework import permissions
from django.db import transaction
from django.utils import timezone

# custom permission to only allow participants of an interview to view it.
class IsInterviewParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the user is either the interviewer or interviewee
        return obj.interviewer == request.user or obj.interviewee == request.user

# Helper validation functions
def is_valid_availability(availability):
    return isinstance(availability, list) and len(availability) == 48 and all(isinstance(slot, bool) for slot in availability)

# Create your views here.
class AuthenticatedMemberSignupForInterview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            _ = InterviewPool.objects.get(member=request.user)
            return Response(
                {
                    "sign_up": True,
                    "detail": "You are signed up for an interview.",
                    "member": request.user.username
                },
                status=status.HTTP_200_OK
            )
        except InterviewPool.DoesNotExist:
            return Response(
                {
                    "sign_up": False,
                    "detail": "You are not signed up for an interview.",
                    "member": request.user.username
                },
                status=status.HTTP_200_OK
            )

    def post(self, request):
        # Get or create InterviewAvailability for the user
        interview_availability, _ = InterviewAvailability.objects.get_or_create(
            member=request.user,
        )

        # Update availability if provided in the request
        if 'availability' in request.data:
            new_availability = request.data['availability']
            try:
                interview_availability.set_interview_availability(new_availability)
            except ValidationError as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Check if user is already in InterviewPool
        try:
            InterviewPool.objects.get(member=request.user)
            interview_availability.save()
            return Response(
                {"detail": "You have successfully updated your interview availability."},
                status=status.HTTP_200_OK
            )

        except InterviewPool.DoesNotExist:
            # If user is not in pool, add them and save availability
            InterviewPool.objects.create(member=request.user)
            interview_availability.save()
            return Response(
                {"detail": "You have successfully signed up for an interview."},
                status=status.HTTP_201_CREATED
            )

    def delete(self, request):
        try:
            interview_pool = InterviewPool.objects.get(member=request.user)
            interview_pool.delete()
            return Response(
                {"detail": "You have successfully cancelled your interview."}
            )
        except InterviewPool.DoesNotExist:
            return Response(
                {"detail": "You are not signed up for an interview."},
                status=status.HTTP_400_BAD_REQUEST
            )


class GetInterviewPoolStatus(APIView):
    # TODO: Change permission class to isAdminUser
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            interview_pool = InterviewPool.objects.all()
            return Response({
                "number_sign_up": len(interview_pool),
                "members": [
                    member.member.username
                    for member in interview_pool
                ]
            })
        except InterviewPool.DoesNotExist:
            return Response({"number_sign_up": 0, "members": []})

class PairInterview(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pairing_algorithm = CommonAvailabilityStableMatching()

    @transaction.atomic
    def post(self, request):
        pool_members = list(InterviewPool.objects.all())

        if len(pool_members) < 2:
            return Response({"detail": "Not enough members in the pool to pair interviews."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Get availabilities for all members
        availabilities = {
            member.member.id: InterviewAvailability.objects.get(member=member.member).interview_availability_slots or [[False] * 48 for _ in range(7)]
            for member in pool_members
        }

        pool_member_ids = [m.member.id for m in pool_members]
        self.pairing_algorithm.set_availabilities(availabilities)
        # Perform pairing using the CommonAvailabilityStableMatching algorithm
        matches = self.pairing_algorithm.pair(pool_member_ids)

        # Create interviews based on matches
        paired_interviews = []
        for i, j in enumerate(matches):
            if i < j:  # Avoid creating duplicate interviews
                p1 = pool_members[i].member
                p2 = pool_members[j].member

                interview1 = Interview.objects.create(
                    interviewer=p1,
                    interviewee=p2,
                    status='pending',
                    date_effective=timezone.now(),
                )

                interview2 = Interview.objects.create(
                    interviewer=p2,
                    interviewee=p1,
                    status='pending',
                    date_effective=timezone.now(),
                )

                paired_interviews.append(interview1)
                paired_interviews.append(interview2)

                # Remove paired users from the pool
                InterviewPool.objects.filter(member__in=[p1, p2]).delete()

        # Check for any unpaired members
        unpaired_members = [member.member.username for i, member in enumerate(pool_members) if matches[i] == -1]

        return Response({
            "detail": f"Successfully paired {len(paired_interviews)} interviews.",
            "paired_interviews": [
                {
                    "interview_id": str(interview.interview_id),
                    "interviewer": interview.interviewer.username,
                    "interviewee": interview.interviewee.username
                } for interview in paired_interviews
            ],
            "unpaired_members": unpaired_members
        }, status=status.HTTP_201_CREATED)


class NotifyInterview(APIView):
    # TODO: Change permission class to isAdminUser or using a key service
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # TODO: Implement the notification service
        return Response({"detail": "Notification sent."})


class InterviewQuestions(APIView):
    # TODO: Change permission class to isAdminUser
    permission_classes = [IsAuthenticated]

    def get(self, request, interview_id):
        try:
            interview = Interview.objects.get(interview_id=interview_id)
            return Response(
                {
                    "interview_id": interview.interview_id,
                    "technical_question": (
                        interview.technical_question.question
                    ),
                    "behavioral_questions": [
                        question.question
                        for question in interview.behavioral_questions.all()
                    ],
                }
            )
        except Interview.DoesNotExist:
            return Response(
                {"detail": "Interview not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class InterviewRunningStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, interview_id):
        try:
            interview = Interview.objects.get(
                interviewer=request.user,
                interview_id=interview_id,
                status='active'
            )
            return Response(
                {
                    "interview_id": interview.interview_id,
                    "interviewee": interview.interviewee.username,
                    "status": interview.status,
                    "date_effective": interview.date_effective,
                    "date_completed": interview.date_completed,
                }
            )
        except Interview.DoesNotExist:
            return Response(
                {"detail": "No active interview found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, interview_id):
        try:
            interview = Interview.objects.get(
                interviewer=request.user,
                interview_id=interview_id,
                status='active'
            )
            # Note: This is a simple implementation to complete the interview,
            # not quite sure best way to handle this
            interview.status = 'inactive'
            interview.save()
            return Response(
                {"detail": "Interview completed."},
                status=status.HTTP_200_OK
            )
        except Interview.DoesNotExist:
            return Response(
                {"detail": "No active interview found."},
                status=status.HTTP_404_NOT_FOUND
            )
class MemberInterviewsView(generics.ListAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Interview.objects.filter(interviewer=user) | Interview.objects.filter(interviewee=user)

class InterviewerInterviewsView(generics.ListAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Interview.objects.filter(interviewer=self.request.user)

class IntervieweeInterviewsView(generics.ListAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Interview.objects.filter(interviewee=self.request.user)

class InterviewDetailView(generics.RetrieveAPIView):
    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated, IsInterviewParticipant]
    lookup_field = 'interview_id'

    def get_queryset(self):
        user = self.request.user
        return Interview.objects.filter(interviewer=user) | Interview.objects.filter(interviewee=user)