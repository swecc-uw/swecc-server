from django.urls import path
from . import views

urlpatterns = [
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
        'interviews/',
        views.MemberInterviewsView.as_view(),
        name='member-interviews'
    ),
    path(
        'interviews/interviewer/',
        views.InterviewerInterviewsView.as_view(),
        name='interviewer-interviews'
    ),
    path(
        'interviews/interviewee/',
        views.IntervieweeInterviewsView.as_view(),
        name='interviewee-interviews'
    ),
    path(
        'interviews/<uuid:interview_id>/',
        views.InterviewDetailView.as_view(),
        name='interview-detail'
    ),
    path(
        'availability/',
        views.InterviewAvailabilityView.as_view(),
        name='interview-availability'
    ),
]
