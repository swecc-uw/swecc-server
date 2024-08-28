from django.urls import path
from . import views

urlpatterns = [
    path(
        "all/",
        views.InterviewAll.as_view(),
        name="interviewer-list-create"
    ),
    path(
        "pair/",
        views.PairInterview.as_view(),
        name="pair-interviews"
    ),
    path(
        "pool/",
        views.AuthenticatedMemberSignupForInterview.as_view(),
        name="interview-pool"
    ),
    path(
        "status/",
        views.GetInterviewPoolStatus.as_view(),
        name="interview-pool-status"
    ),
    path(
        'mine/',
        views.InterviewDetailViewAsUser.as_view(),
        name='interview-detail-user'
    ),
    path(
        '/<uuid:interview_id>/',
        views.InterviewDetailViewAsAdmin.as_view(),
        name='interview-detail-admin'
    ),
    path(
        'availability/',
        views.InterviewAvailabilityView.as_view(),
        name='interview-availability'
    ),
    path(
        "assign/",
        views.InterviewAssignQuestionRandom.as_view(),
        name="assign-interview-question"
    ),
    path(
        "assign/<uuid:interview_id>/",
        views.InterviewAssignQuestionRandomIndividual.as_view(),
        name="assign-interview-question"
    )
]
