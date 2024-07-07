from django.urls import path
from . import views

urlpatterns = [
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
]
