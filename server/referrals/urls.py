from django.urls import path

from . import views

urlpatterns = [
    path("", views.ListCreateReferralView.as_view(), name="referral-list-create"),
    path("<int:pk>/", views.ReferralDetailView.as_view(), name="referral-detail"),
    path(
        "<int:referral_id>/upload/",
        views.DocumentUploadView.as_view(),
        name="referral-upload",
    ),
    path(
        "<int:referral_id>/review/",
        views.ReferralReviewView.as_view(),
        name="referral-review",
    ),
    path(
        "pending/", views.MyPendingReferralsView.as_view(), name="my-pending-referrals"
    ),
]
