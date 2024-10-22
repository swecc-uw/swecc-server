from datetime import datetime
from datetime import datetime
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from questions.models import TechnicalQuestion, BehavioralQuestion
from custom_auth.permissions import IsAdmin
from .algorithm import CommonAvailabilityStableMatching
from .notification import interview_paired_notification_html, interview_unpaired_notification_html, send_email
from .models import Interview
from .serializers import InterviewSerializer
from .models import InterviewAvailability, InterviewPool, Interview
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from rest_framework import permissions
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

INTERVIEW_NOTIFICATION_ADDR = "interview@no-reply.swecc.org"
# number of technical questionp assign per pair
INTERVIEW_NUM_TECHNICAL_QUESTIONS = 3

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


# Create your views here.
class AuthenticatedMemberSignupForInterview(APIView):
    permission_classes = [IsAuthenticated]

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
            InterviewPool.objects.get(member=request.user)
            interview_availability.save()
            logger.info(
                f"User {request.user.username} updated their interview availability"
            )
            return Response(
                {
                    "detail": "You have successfully updated your interview availability."
                },
                status=status.HTTP_200_OK,
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
                request.user.username
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
            logger.info("Interview pool status: %d members signed up", len(interview_pool))
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

        if len(pool_members) < 2:
            logger.warning("Not enough members in the pool to pair interviews")
            return Response(
                {"detail": "Not enough members in the pool to pair interviews."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get availabilities for all members
        availabilities = {
            member.member.id: InterviewAvailability.objects.get(
                member=member.member
            ).interview_availability_slots
            or [[False] * 48 for _ in range(7)]
            for member in pool_members
        }

        pool_member_ids = [m.member.id for m in pool_members]
        logger.info("Pairing interviews for %d members", len(pool_member_ids))
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
                    status="pending",
                    date_effective=timezone.now(),
                )

                interview2 = Interview.objects.create(
                    interviewer=p2,
                    interviewee=p1,
                    status="pending",
                    date_effective=timezone.now(),
                )

                paired_interviews.append(interview1)
                paired_interviews.append(interview2)

                # Remove paired users from the pool
                InterviewPool.objects.filter(member__in=[p1, p2]).delete()

        logger.info("Paired %d interviews", len(paired_interviews))
        # Check for any unpaired members
        unpaired_members = [member for i, member in enumerate(pool_members) if matches[i] == -1]

        failed_paired_emails = []
        # notifications
        logger.info("Sending notifications to %d paired members", len(paired_interviews))
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
                        interview_date=interview.date_effective
                    )
                )
            except Exception as e:
                failed_paired_emails.append((interview.interview_id, interview.interviewer.email, str(e)))

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
                        interview_date=interview.date_effective
                    )
                )
            except Exception as e:
                failed_paired_emails.append((interview.interview_id, interview.interviewee.email, str(e)))

        logger.error("Failed to send notifications to %d paired members", len(failed_paired_emails))
        logger.info("Sending notifications to %d unpaired members", len(unpaired_members))
        failed_unpaired_emails = []
        for pool_member in unpaired_members:
            try:
                send_email(
                    from_email=INTERVIEW_NOTIFICATION_ADDR,
                    to_email=pool_member.member.email,
                    subject="You have not been paired for an upcoming mock interview",
                    html_content=interview_unpaired_notification_html(
                        pool_member.member.first_name,
                        timezone.now().strftime("%B %d, %Y")
                    )
                )
            except Exception as e:
                failed_unpaired_emails.append((pool_member.member.email, str(e)))

        logger.error("Failed to send notifications to %d unpaired members", len(failed_unpaired_emails))

        unpaired_members = [
            member.member.username
            for i, member in enumerate(pool_members)
            if matches[i] == -1
        ]

        logger.info(
            "Successfully paired %d interviews. Unpaired members: {len(unpaired_members)}",
            len(paired_interviews)
        )
        return Response(
            {
                "detail": f"Successfully paired {len(paired_interviews)} interviews.",
                "paired_interviews": [
                    {
                        "interview_id": str(interview.interview_id),
                        "interviewer": interview.interviewer.username,
                        "interviewee": interview.interviewee.username,
                    }
                    for interview in paired_interviews
                ],
                "unpaired_members": unpaired_members,
                # "failed_paired_emails": failed_paired_emails,
                # "failed_unpaired_emails": failed_unpaired_emails,
            },
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        logger.info("GET request received for PairInterview")
        return Response({"detail": "This endpoint is for pairing interviews. Use POST to pair interviews."})


class InterviewAll(APIView):
    permission_classes = [IsAdmin]
    
    def get(self, request):
        # Check if there are no interviews
        interviews = Interview.objects.all()
        if not interviews.exists():
            return Response(
                {"detail": "No interviews found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize the interview data
        serializer = InterviewSerializer(interviews, many=True)
        return Response(
            {"interviews": serializer.data},
            status=status.HTTP_200_OK
        )


class InterviewAssignQuestionRandom(APIView):
    permission_classes = [IsAdmin]
    def post(self, request):
        try:
            # find all interview within this week (from last monday to next monday)
            today = timezone.now()
            last_monday = today - timezone.timedelta(days=today.weekday())
            next_next_monday = last_monday + timezone.timedelta(days=14)
            interviews = Interview.objects.filter(date_effective__gte=last_monday, date_effective__lte=next_next_monday)

            if not interviews.exists():
                return Response(
                    {"detail": "No interviews found for this week."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            technicalQ = TechnicalQuestion.objects.order_by("?").first()
            behavioralQ = BehavioralQuestion.objects.order_by("?")[:INTERVIEW_NUM_TECHNICAL_QUESTIONS]
            
            for interview in interviews:
                interview.technical_question = technicalQ
                interview.behavioral_questions.set(behavioralQ)
                interview.save()

            return Response(
                {"detail": "Questions assigned."},
                status=status.HTTP_201_OK
            )
        except len(interviews) == 0:
            return Response(
                {"detail": "Interview not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class InterviewAssignQuestionRandomIndividual(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, interview_id):
        try:
            interview = Interview.objects.get(interview_id=interview_id)
            technicalQ = TechnicalQuestion.objects.order_by("?").first()
            behavioralQ = BehavioralQuestion.objects.order_by("?")[:3]
            interview.technical_question = technicalQ
            interview.behavioral_questions.set(behavioralQ)
            interview.save()
            return Response(
                {"detail": "Questions assigned."},
                status=status.HTTP_200_OK
            )
        except Interview.DoesNotExist:
            return Response(
                {"detail": "Interview not found."},
                status=status.HTTP_404_NOT_FOUND
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
                    "technical_question": (interview.technical_question.question),
                    "behavioral_questions": [
                        question.question
                        for question in interview.behavioral_questions.all()
                    ],
                }
            )
        except Interview.DoesNotExist:
            logger.error("Interview not found. ID: %s", interview_id)
            return Response(
                {"detail": "Interview not found."}, status=status.HTTP_404_NOT_FOUND
            )


class InterviewRunningStatus(APIView):
    permission_classes = [IsAuthenticated]

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
            logger.warning("No active interview found to complete. ID: %s", interview_id)
            return Response(
                {"detail": "No active interview found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class MemberInterviewsView(generics.ListAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        logger.info("Retrieving interviews for user: %s", user.username)
        return Interview.objects.filter(interviewer=user) | Interview.objects.filter(
            interviewee=user
        )


class InterviewerInterviewsView(generics.ListAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'interview_id'

    def get_queryset(self):
        logger.info(
            "Retrieving interviews where user is interviewer: %s",
            self.request.user.username
        )
        return Interview.objects.filter(interviewer=self.request.user)


class IntervieweeInterviewsView(generics.ListAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.info(
            f"Retrieving interviews where user is interviewee: {self.request.user.username}"
        )
        return Interview.objects.filter(interviewee=self.request.user)


class InterviewDetailView(generics.RetrieveAPIView):
    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated, IsInterviewParticipant]
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
        if interview.interviewer != user and interview.status != 'completed':
            interview_data.pop("technical_question", None)
            interview_data.pop("behavioral_questions", None)

        return interview_data


class InterviewAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated, IsInterviewParticipant]

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
                    {"detail": "Cannot propose time for this interview. Status: {interview.status}"},
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
                {"detail": "Interview time proposed successfully.", "interview": updated_interview_serialized},
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
    permission_classes = [IsAuthenticated, IsInterviewParticipant]

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
                logger.warning("Commit time does not match proposed time, proposed: %s, commit: %s", interview.proposed_time, commit_time)
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
                {"detail": "Interview committed successfully.", "interview": updated_interview_serialized},
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
    permission_classes = [IsAuthenticated, IsInterviewParticipant]

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
                        completion_time = parse_date(
                            completion_time
                        )
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
                    "interview": updated_interview_serialized
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
