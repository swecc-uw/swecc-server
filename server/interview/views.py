from datetime import datetime, timedelta
from django.utils import timezone
import random
from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Max, Q
from django.core.exceptions import ValidationError
from django.db import transaction
import logging

import server.settings as settings
from questions.models import (
    TechnicalQuestion,
    BehavioralQuestion,
    TechnicalQuestionQueue,
)
from custom_auth.permissions import IsAdmin, IsVerified
from members.serializers import UserSerializer
from members.models import User
from questions.serializers import (
    BehavioralQuestionSerializer,
    TechnicalQuestionSerializer,
)
from .algorithm import CommonAvailabilityStableMatching
from .notification import (
    interview_paired_notification_html,
    interview_unpaired_notification_html,
    send_email,
)
from .models import Interview, InterviewAvailability, InterviewPool
from .serializers import InterviewSerializer

logger = logging.getLogger(__name__)

INTERVIEW_NOTIFICATION_ADDR = "interview@no-reply.swecc.org"
# number of technical questionp assign per pair
INTERVIEW_NUM_BEHAVIORAL_QUESTIONS = 3
INTERVIEW_NUM_TECHNICAL_QUESTIONS = 1


def parse_date(x):
    date = datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ")

    if timezone.is_aware(date):
        return date
    return timezone.make_aware(date)


# custom permission to only allow participants of an interview to view it.
class IsInterviewParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the user is either the interviewer or interviewee
        return obj.interviewer == request.user or obj.interviewee == request.user


# Helper validation functions
def is_valid_availability(availability):
    return (
        isinstance(availability, list)
        and len(availability) == 48
        and all(isinstance(slot, bool) for slot in availability)
    )


class GetSignupData(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 14))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        signups = InterviewPool.objects.filter(
            timestamp__isnull=False, timestamp__gte=start_date, timestamp__lte=end_date
        ).values("member__username", "member_id", "timestamp")

        signup_data = [
            {
                "username": signup["member__username"],
                "user_id": signup["member_id"],
                "timestamp": int(signup["timestamp"].timestamp() * 1000),
            }
            for signup in signups
        ]

        return Response(signup_data)


# Create your views here.
class AuthenticatedMemberSignupForInterview(APIView):
    permission_classes = [IsAuthenticated, IsVerified]

    def get(self, request):
        logger.info(
            f"GET request received for AuthenticatedMemberSignupForInterview by user {request.user.username}"
        )
        try:
            _ = InterviewPool.objects.get(member=request.user)
            logger.info(
                f"User {request.user.username} is already signed up for an interview"
            )
            return Response(
                {
                    "sign_up": True,
                    "detail": "You are signed up for an interview.",
                    "member": request.user.username,
                },
                status=status.HTTP_200_OK,
            )
        except InterviewPool.DoesNotExist:
            logger.info(
                f"User {request.user.username} is not signed up for an interview"
            )
            return Response(
                {
                    "sign_up": False,
                    "detail": "You are not signed up for an interview.",
                    "member": request.user.username,
                },
                status=status.HTTP_200_OK,
            )

    def post(self, request):
        logger.info(
            f"POST request received for AuthenticatedMemberSignupForInterview by user {request.user.username}"
        )
        # Get or create InterviewAvailability for the user
        interview_availability, _ = InterviewAvailability.objects.get_or_create(
            member=request.user,
        )

        # Update availability if provided in the request
        if "availability" in request.data:
            new_availability = request.data["availability"]
            try:
                interview_availability.set_interview_availability(new_availability)
            except ValidationError as e:
                logger.error(
                    f"Validation error for user {request.user.username}: {str(e)}"
                )
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user is already in InterviewPool
        try:

            ent = InterviewPool.objects.get(member=request.user)
            ent.timestamp = timezone.now()
            ent.save()
            interview_availability.save()
            logger.info(
                "User %s signed up for an interview at %s",
                request.user.username,
                ent.timestamp.isoformat(),
            )
            return Response(
                {"detail": "You have successfully signed up for an interview."},
                status=status.HTTP_201_CREATED,
            )

        except InterviewPool.DoesNotExist:
            # If user is not in pool, add them and save availability
            InterviewPool.objects.create(member=request.user)
            interview_availability.save()
            logger.info("User %s signed up for an interview", request.user.username)
            return Response(
                {"detail": "You have successfully signed up for an interview."},
                status=status.HTTP_201_CREATED,
            )

    def delete(self, request):
        logger.info(
            f"DELETE request received for AuthenticatedMemberSignupForInterview by user {request.user.username}"
        )
        try:
            interview_pool = InterviewPool.objects.get(member=request.user)
            interview_pool.delete()
            logger.info("User %s cancelled their interview", request.user.username)
            return Response(
                {"detail": "You have successfully cancelled your interview."}
            )
        except InterviewPool.DoesNotExist:
            logger.warning(
                "User %s attempted to cancel a non-existent interview",
                request.user.username,
            )
            return Response(
                {"detail": "You are not signed up for an interview."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class GetInterviewPoolStatus(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        logger.info("GET request received for GetInterviewPoolStatus")
        try:
            interview_pool = InterviewPool.objects.all()
            logger.info(
                "Interview pool status: %d members signed up", len(interview_pool)
            )
            return Response(
                {
                    "number_sign_up": len(interview_pool),
                    "members": [member.member.username for member in interview_pool],
                }
            )
        except InterviewPool.DoesNotExist:
            logger.info("Interview pool is empty")
            return Response({"number_sign_up": 0, "members": []})


class PairInterview(APIView):
    permission_classes = [IsAdmin]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pairing_algorithm = CommonAvailabilityStableMatching()

    @transaction.atomic
    def post(self, request):
        logger.info("POST request received for PairInterview")
        pool_members = list(InterviewPool.objects.all())

        if len(pool_members) % 2 != 0:
            random_idx_of_death = random.randint(0, len(pool_members) - 1)
            rip = pool_members.pop(random_idx_of_death)
            logger.warning(
                "Number of members in the pool must be even. Removing one member: %s, id: %s",
                rip.member.username,
                rip.member.id,
            )

        if len(pool_members) < 2:
            logger.warning("Not enough members in the pool to pair interviews")
            return Response(
                {"detail": "Not enough members in the pool to pair interviews."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get availabilities for all members
        availabilities = {
            member.member.id: (
                InterviewAvailability.objects.get(
                    member=member.member
                ).interview_availability_slots
                if InterviewAvailability.objects.filter(member=member.member).exists()
                else [[False] * 48 for _ in range(7)]
            )
            for member in pool_members
        }

        pool_member_ids = [m.member.id for m in pool_members]
        logger.info("Pairing interviews for %d members", len(pool_member_ids))
        self.pairing_algorithm.set_availabilities(availabilities)
        matching_result = self.pairing_algorithm.pair(pool_member_ids)

        # Create interviews based on matches
        # find all interview within this week (from last monday to next monday)
        today = timezone.now()
        last_monday = today - timezone.timedelta(days=today.weekday())
        last_monday = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        next_next_monday = last_monday + timezone.timedelta(days=14)

        paired_interviews = []

        Interview.objects.filter(
            date_effective__gte=last_monday, date_effective__lte=next_next_monday
        ).delete()

        # Get questions from queue
        tqs = TechnicalQuestionQueue.objects.all().order_by("position")

        if len(tqs) < 2:
            logger.warning("Not enough questions in the queue to assign interviews")
            return Response(
                {"detail": "Not enough questions in the queue to assign interviews."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the lowest position to ensure we get consecutive questions
        low = tqs.first().position

        # Get the two questions at consecutive positions
        question_queues = [tqs.filter(position=low + i).first() for i in range(2)]
        technical_questions = [tq.question for tq in question_queues if tq]
        logger.info("Paired interviews will have questions: %s", technical_questions)
        if len(technical_questions) < 2:
            return Response(
                {"detail": "Could not find consecutive questions in the queue."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        matches = matching_result.pairs
        logger.info("Common slots matrix shape: %s", matching_result.common_slots.shape)
        logger.info("Number of preference scores: %d", len(matching_result.preference_scores))

        for i, j in enumerate(matches):
            if i < j:  # Avoid creating duplicate interviews
                p1 = pool_members[i].member
                p2 = pool_members[j].member

                common_slots_count = matching_result.common_slots[i, j]
                logger.info(
                    "Creating interview pair with %d common slots: %s and %s",
                    common_slots_count,
                    p1.username,
                    p2.username
                )

                interview1 = Interview.objects.create(
                    interviewer=p1,
                    interviewee=p2,
                    status="pending",
                    date_effective=timezone.now(),
                )
                interview1.technical_questions.add(technical_questions[0])

                interview2 = Interview.objects.create(
                    interviewer=p2,
                    interviewee=p1,
                    status="pending",
                    date_effective=timezone.now(),
                )
                interview2.technical_questions.add(technical_questions[1])

                paired_interviews.append(interview1)
                paired_interviews.append(interview2)

                # remove paired users from the pool
                InterviewPool.objects.filter(member__in=[p1, p2]).delete()

        # update question positions in queue
        new_position = (
            TechnicalQuestionQueue.objects.aggregate(Max("position"))["position__max"]
            + 1
        )
        for tq in question_queues:
            tq.position = new_position
            tq.save()
            new_position += 1

        logger.info("Paired %d interviews", len(paired_interviews))
        # check for any unpaired members
        unpaired_members = InterviewPool.objects.all()

        failed_paired_emails = []
        # notifications
        logger.info(
            "Sending notifications to %d paired members", len(paired_interviews)
        )
        if not settings.DJANGO_DEBUG:
            logger.info("DEBUG is off, sending emails")
            for interview in paired_interviews:
                try:
                    send_email(
                        from_email=INTERVIEW_NOTIFICATION_ADDR,
                        to_email=interview.interviewer.email,
                        subject="You've been paired for an upcoming mock interview!",
                        html_content=interview_paired_notification_html(
                            name=interview.interviewer.first_name,
                            partner_name=interview.interviewee.first_name,
                            partner_email=interview.interviewee.email,
                            partner_discord_id=interview.interviewee.discord_id,
                            partner_discord_username=interview.interviewee.discord_username,
                            interview_date=interview.date_effective,
                        ),
                    )
                except Exception as e:
                    failed_paired_emails.append(
                        (interview.interview_id, interview.interviewer.email, str(e))
                    )

                try:
                    send_email(
                        from_email=INTERVIEW_NOTIFICATION_ADDR,
                        to_email=interview.interviewee.email,
                        subject="You've been paired for an upcoming mock interview!",
                        html_content=interview_paired_notification_html(
                            name=interview.interviewee.first_name,
                            partner_name=interview.interviewer.first_name,
                            partner_email=interview.interviewer.email,
                            partner_discord_id=interview.interviewer.discord_id,
                            partner_discord_username=interview.interviewer.discord_username,
                            interview_date=interview.date_effective,
                        ),
                    )
                except Exception as e:
                    failed_paired_emails.append(
                        (interview.interview_id, interview.interviewee.email, str(e))
                    )
        else:
            logger.info("DEBUG is on, not sending emails")

        logger.error(
            "Failed to send notifications to %d paired members",
            len(failed_paired_emails),
        )
        logger.info(
            "Sending notifications to %d unpaired members", len(unpaired_members)
        )
        failed_unpaired_emails = []
        if not settings.DJANGO_DEBUG:
            logger.info("DEBUG is off, sending emails")
            for pool_member in unpaired_members:
                try:
                    send_email(
                        from_email=INTERVIEW_NOTIFICATION_ADDR,
                        to_email=pool_member.member.email,
                        subject="You have not been paired for an upcoming mock interview",
                        html_content=interview_unpaired_notification_html(
                            pool_member.member.first_name,
                            timezone.now().strftime("%B %d, %Y"),
                        ),
                    )
                except Exception as e:
                    failed_unpaired_emails.append((pool_member.member.email, str(e)))
        else:
            logger.info("DEBUG is on, not sending emails")
        logger.error(
            "Failed to send notifications to %d unpaired members",
            len(failed_unpaired_emails),
        )

        unpaired_members_username = [
            member.member.username for member in unpaired_members
        ]

        logger.info(
            "Successfully paired %d interviews. Unpaired members: %d",
            len(paired_interviews),
            len(unpaired_members),
        )
        return Response(
            {
                "detail": f"Successfully paired {len(paired_interviews)} interviews.",
                "paired_interviews": [
                    {
                        "interview_id": str(interview.interview_id),
                        "interviewer": interview.interviewer.username,
                        "interviewee": interview.interviewee.username,
                        "common_slots": matching_result.common_slots[
                            pool_member_ids.index(interview.interviewer.id),
                            pool_member_ids.index(interview.interviewee.id)
                        ]
                    }
                    for interview in paired_interviews
                ],
                "unpaired_members": unpaired_members_username,
                "failed_paired_emails": failed_paired_emails,
                "failed_unpaired_emails": failed_unpaired_emails,
            },
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        logger.info("GET request received for PairInterview")
        return Response(
            {
                "detail": "This endpoint is for pairing interviews. Use POST to pair interviews."
            }
        )


class InterviewAll(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        # Check if there are no interviews
        interviews = Interview.objects.all()
        if not interviews.exists():
            return Response(
                {"detail": "No interviews found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Serialize the interview data
        serializer = InterviewSerializer(interviews, many=True)
        return Response({"interviews": serializer.data}, status=status.HTTP_200_OK)


class InterviewAssignQuestionRandom(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        try:
            # find all interview within this week (from last monday to next monday)
            today = timezone.now()
            last_monday = today - timezone.timedelta(days=today.weekday())
            last_monday = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            next_next_monday = last_monday + timezone.timedelta(days=14)
            interviews = Interview.objects.filter(
                date_effective__gte=last_monday, date_effective__lte=next_next_monday
            )

            logger.info("Assiged period from %s to %s", last_monday, next_next_monday)
            logger.info("Assigning questions to %d interviews", len(interviews))

            if not interviews.exists():
                return Response(
                    {"detail": "No interviews found for this week."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            technicalQ = TechnicalQuestion.objects.order_by("?")[
                :INTERVIEW_NUM_TECHNICAL_QUESTIONS
            ]
            behavioralQ = BehavioralQuestion.objects.order_by("?")[
                :INTERVIEW_NUM_BEHAVIORAL_QUESTIONS
            ]

            for interview in interviews:
                interview.technical_questions.add(*technicalQ)
                interview.behavioral_questions.add(*behavioralQ)
                interview.save()

            return Response(
                {"detail": "Questions assigned."}, status=status.HTTP_201_CREATED
            )
        except not interviews:
            return Response(
                {"detail": "Interview not found."}, status=status.HTTP_404_NOT_FOUND
            )


class InterviewAssignQuestionRandomIndividual(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, interview_id):
        try:
            interview = Interview.objects.get(interview_id=interview_id)
            technicalQ = TechnicalQuestion.objects.order_by("?")[
                :INTERVIEW_NUM_TECHNICAL_QUESTIONS
            ]
            behavioralQ = BehavioralQuestion.objects.order_by("?")[
                :INTERVIEW_NUM_BEHAVIORAL_QUESTIONS
            ]
            interview.technical_questions.set(technicalQ)
            interview.behavioral_questions.set(behavioralQ)
            interview.save()
            return Response(
                {"detail": "Questions assigned."}, status=status.HTTP_200_OK
            )
        except Interview.DoesNotExist:
            return Response(
                {"detail": "Interview not found."}, status=status.HTTP_404_NOT_FOUND
            )


class InterviewQuestions(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, interview_id):
        logger.info(
            f"GET request received for InterviewQuestions. Interview ID: {interview_id}"
        )
        try:
            interview = Interview.objects.get(interview_id=interview_id)
            logger.info("Retrieved questions for interview ID: %s", interview_id)
            return Response(
                {
                    "interview_id": interview.interview_id,
                    "technical_questions": [
                        question for question in interview.technical_questions.all()
                    ],
                    "behavioral_questions": [
                        question for question in interview.behavioral_questions.all()
                    ],
                }
            )
        except Interview.DoesNotExist:
            logger.error("Interview not found. ID: %s", interview_id)
            return Response(
                {"detail": "Interview not found."}, status=status.HTTP_404_NOT_FOUND
            )


class InterviewRunningStatus(APIView):
    permission_classes = [IsAuthenticated, IsVerified]

    def get(self, request, interview_id):
        logger.info(
            f"GET request received for InterviewRunningStatus. Interview ID: {interview_id}"
        )
        try:
            interview = Interview.objects.get(
                interviewer=request.user, interview_id=interview_id, status="active"
            )
            logger.info("Retrieved active interview status. ID: %s", interview_id)
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
            logger.warning("No active interview found. ID: %s", interview_id)
            return Response(
                {"detail": "No active interview found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def put(self, request, interview_id):
        logger.info(
            f"PUT request received for InterviewRunningStatus. Interview ID: {interview_id}"
        )
        try:
            interview = Interview.objects.get(
                interviewer=request.user, interview_id=interview_id, status="active"
            )
            # Note: This is a simple implementation to complete the interview,
            # not quite sure best way to handle this
            interview.status = "inactive"
            interview.save()
            logger.info("Interview completed. ID: %s", interview_id)
            return Response(
                {"detail": "Interview completed."}, status=status.HTTP_200_OK
            )
        except Interview.DoesNotExist:
            logger.warning(
                "No active interview found to complete. ID: %s", interview_id
            )
            return Response(
                {"detail": "No active interview found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class MemberInterviewsView(generics.ListAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated, IsVerified]

    def get_queryset(self):
        user = self.request.user
        logger.info("Retrieving interviews for user: %s", user.username)
        return Interview.objects.filter(interviewer=user) | Interview.objects.filter(
            interviewee=user
        )


class InterviewerInterviewsView(generics.ListAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAdmin]
    lookup_field = "interview_id"

    def get_queryset(self):
        logger.info(
            "Retrieving interviews where user is interviewer: %s",
            self.request.user.username,
        )
        return Interview.objects.filter(interviewer=self.request.user)


class IntervieweeInterviewsView(generics.ListAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated, IsVerified]

    def get_queryset(self):
        logger.info(
            f"Retrieving interviews where user is interviewee: {self.request.user.username}"
        )
        return Interview.objects.filter(interviewee=self.request.user)


class InterviewDetailView(generics.RetrieveAPIView):
    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated, IsInterviewParticipant, IsVerified]
    lookup_field = "interview_id"

    def get_queryset(self):
        user = self.request.user
        logger.info("Retrieving interview details for user: %s", user.username)
        return Interview.objects.filter(interviewer=user) | Interview.objects.filter(
            interviewee=user
        )

    def _format_interview_data(self, interview, user):
        # Prepare interview data based on user role and interview status
        serializer = InterviewSerializer(interview)

        interview_data = serializer.data

        # Remove questions if user role and status conditions are met
        if interview.interviewer != user and interview.status != "completed":
            interview_data.pop("technical_questions", None)
            interview_data.pop("behavioral_questions", None)
        else:
            interview_data["technical_questions"] = [
                question for question in interview.technical_questions.all()
            ]
            interview_data["behavioral_questions"] = [
                question for question in interview.behavioral_questions.all()
            ]

        return interview_data


class InterviewAvailabilityView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]

    def get(self, request):
        logger.info(
            f"GET request received for InterviewAvailabilityView. User: {request.user.username}"
        )
        try:
            interview_availability = InterviewAvailability.objects.get(
                member=request.user
            )
            logger.info(
                f"Retrieved interview availability for user: {request.user.username}"
            )
            return Response(
                {
                    "id": request.user.id,
                    "availability": interview_availability.interview_availability_slots,
                },
                status=status.HTTP_200_OK,
            )
        except InterviewAvailability.DoesNotExist:
            logger.warning(
                f"Interview availability not found for user: {request.user.username}"
            )
            return Response(
                {"detail": "Interview availability not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request):
        logger.info(
            f"POST request received for InterviewAvailabilityView. User: {request.user.username}"
        )
        try:
            interview_availability = InterviewAvailability.objects.get(
                member=request.user
            )
            availability = request.data.get("availability")

            if not is_valid_availability(availability):
                logger.error(
                    f"Invalid availability format provided by user: {request.user.username}"
                )
                return Response(
                    {"detail": "Invalid availability format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            interview_availability.set_interview_availability(availability)
            interview_availability.save()

            logger.info(
                f"Interview availability updated for user: {request.user.username}"
            )
            return Response(
                {"detail": "Interview availability updated."}, status=status.HTTP_200_OK
            )
        except InterviewAvailability.DoesNotExist:
            logger.warning(
                f"Interview availability not found for user: {request.user.username}"
            )
            return Response(
                {"detail": "Interview availability not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ProposeView(APIView):
    permission_classes = [IsAuthenticated, IsInterviewParticipant, IsVerified]

    @transaction.atomic
    def post(self, request, interview_id):
        logger.info(
            f"POST request received for ProposeView. Interview ID: {interview_id}"
        )
        try:
            interview = Interview.objects.get(interview_id=interview_id)

            if interview.status not in ["pending", "active"]:
                logger.warning(
                    f"Invalid interview status for proposal. Status: {interview.status}"
                )
                return Response(
                    {
                        "detail": "Cannot propose time for this interview. Status: {interview.status}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            proposed_time = request.data.get("time")
            if not proposed_time:
                logger.warning("No time provided in the request")
                return Response(
                    {"detail": "Time must be provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if isinstance(proposed_time, str):
                try:
                    proposed_time = parse_date(proposed_time)
                except ValueError:
                    logger.warning("Invalid time format provided: %s", proposed_time)
                    return Response(
                        {"detail": "Invalid time format. Please use ISO format."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            interview.proposed_time = proposed_time
            interview.proposed_by = request.user
            interview.status = "pending"
            interview.committed_time = None
            interview.save()

            updated_interview_serialized = InterviewSerializer(interview).data
            logger.info("Interview proposal updated. ID: %s", interview_id)
            return Response(
                {
                    "detail": "Interview time proposed successfully.",
                    "interview": updated_interview_serialized,
                },
                status=status.HTTP_200_OK,
            )

        except Interview.DoesNotExist:
            logger.error("Interview not found. ID: %s", interview_id)
            return Response(
                {"detail": "Interview not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            logger.error("Validation error: %s", str(e))
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CommitView(APIView):
    permission_classes = [IsAuthenticated, IsInterviewParticipant, IsVerified]

    @transaction.atomic
    def post(self, request, interview_id):
        logger.info(
            f"POST request received for CommitView. Interview ID: {interview_id}"
        )
        try:
            interview = Interview.objects.get(interview_id=interview_id)

            if interview.status != "pending":
                logger.warning(
                    f"Invalid interview status for commit. Status: {interview.status}"
                )
                return Response(
                    {"detail": "Cannot commit to this interview."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if interview.proposed_by == request.user:
                logger.warning("User attempting to commit to their own proposal")
                return Response(
                    {"detail": "Cannot commit to your own proposal."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            commit_time = request.data.get("time")
            if not commit_time:
                logger.warning("No time provided in the request")
                return Response(
                    {"detail": "Time must be provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if isinstance(commit_time, str):
                try:
                    commit_time = parse_date(commit_time)
                except ValueError:
                    logger.warning("Invalid time format provided")
                    return Response(
                        {"detail": "Invalid time format. Please use ISO format."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            if commit_time != interview.proposed_time:
                logger.warning(
                    "Commit time does not match proposed time, proposed: %s, commit: %s",
                    interview.proposed_time,
                    commit_time,
                )
                return Response(
                    {"detail": "Commit time must match the proposed time."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            interview.status = "active"
            interview.committed_time = commit_time
            interview.date_effective = timezone.now()
            interview.proposed_time = None
            interview.proposed_by = None
            interview.save()

            updated_interview_serialized = InterviewSerializer(interview).data

            logger.info("Interview committed successfully. ID: %s", interview_id)
            return Response(
                {
                    "detail": "Interview committed successfully.",
                    "interview": updated_interview_serialized,
                },
                status=status.HTTP_200_OK,
            )

        except Interview.DoesNotExist:
            logger.error("Interview not found. ID: %s", interview_id)
            return Response(
                {"detail": "Interview not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            logger.error("Validation error: %s", str(e))
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CompleteView(APIView):
    permission_classes = [IsAuthenticated, IsInterviewParticipant, IsVerified]

    @transaction.atomic
    def post(self, request, interview_id):
        logger.info(
            f"POST request received for CompleteView. Interview ID: {interview_id}"
        )
        try:
            interview = Interview.objects.get(interview_id=interview_id)

            if interview.status != "active":
                logger.warning(
                    f"Invalid interview status for completion. Status: {interview.status}"
                )
                return Response(
                    {"detail": "Cannot complete this interview."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            completion_time = request.data.get("time")
            if completion_time:
                if isinstance(completion_time, str):
                    try:
                        completion_time = parse_date(completion_time)
                    except ValueError:
                        logger.warning("Invalid time format provided")
                        return Response(
                            {"detail": "Invalid time format. Please use ISO format."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                interview.status = "inactive_completed"
                interview.date_completed = completion_time
            else:
                interview.status = "inactive_incomplete"
                interview.date_completed = timezone.now()

            interview.save()

            updated_interview_serialized = InterviewSerializer(interview).data

            logger.info(
                f"Interview marked as {'completed' if completion_time else 'incomplete'}. ID: {interview_id}"
            )
            return Response(
                {
                    "detail": f"Interview marked as {'completed' if completion_time else 'incomplete'}.",
                    "interview": updated_interview_serialized,
                },
                status=status.HTTP_200_OK,
            )

        except Interview.DoesNotExist:
            logger.error("Interview not found. ID: %s", interview_id)
            return Response(
                {"detail": "Interview not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            logger.error("Validation error: %s", str(e))
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserInterviewsDetailView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]

    def get(self, request):
        """
        Fetch all interviews for the authenticated user with hydrated fields.
        Questions are only visible to the interviewer before interview completion.
        """
        logger.info(
            f"GET request received for UserInterviewsDetailView by user {request.user.username}"
        )

        try:
            # all interviews where user is interviewer or interviewee
            interviews = Interview.objects.filter(
                Q(interviewer=request.user) | Q(interviewee=request.user)
            ).select_related("interviewer", "interviewee")

            # hydrate
            processed_interviews = []
            for interview in interviews:
                interview_data = InterviewSerializer(interview).data

                er = User.objects.get(username=interview.interviewer)
                ee = User.objects.get(username=interview.interviewee)

                # interviewer interviewee
                interview_data["interviewer"] = UserSerializer(er).data
                interview_data["interviewee"] = UserSerializer(ee).data

                # question visibility
                is_interviewer = interview.interviewer == request.user
                interview_has_passed = (
                    interview.date_effective + timezone.timedelta(days=7)
                    < timezone.now()
                )
                is_completed = interview.status in [
                    "inactive_completed",
                    "inactive_incomplete",
                ]

                if not (is_interviewer or is_completed or interview_has_passed):
                    interview_data.pop("technical_questions", None)
                    interview_data.pop("behavioral_questions", None)
                else:
                    interview_data["technical_questions"] = [
                        TechnicalQuestionSerializer(question).data
                        for question in interview.technical_questions.all()
                    ]
                    interview_data["behavioral_questions"] = [
                        BehavioralQuestionSerializer(question).data
                        for question in interview.behavioral_questions.all()
                    ]

                processed_interviews.append(interview_data)

            logger.info(
                f"Retrieved {len(processed_interviews)} interviews for user {request.user.username}"
            )
            return Response(
                {"interviews": processed_interviews}, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(
                f"Error fetching interviews for user {request.user.username}: {str(e)}"
            )
            return Response(
                {"detail": "An error occurred while fetching interviews."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
