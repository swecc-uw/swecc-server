from django.urls import path

from . import views

urlpatterns = [
    path("", views.MembersList.as_view(), name="members-list"),
    path(
        "<int:member_id>/",
        views.MemberRetrieveUpdateDestroy.as_view(),
        name="member-retrieve-update-destroy",
    ),
    path(
        "profile/",
        views.AuthenticatedMemberProfile.as_view(),
        name="authenticated-profile",
    ),
    path("verify-discord/", views.UpdateDiscordID.as_view(), name="update-discord-id"),
    path(
        "profile/picture/upload/",
        views.ProfilePictureUploadView.as_view(),
        name="upload_profile_picture",
    ),
    path(
        "reset-password/", views.PasswordResetRequest.as_view(), name="reset-password"
    ),
    path("admin/", views.AdminList.as_view(), name="admin-list"),
    path(
        "update-discord-username",
        views.UpdateDiscordUsername.as_view(),
        name="update-discord-username",
    ),
    path(
        "verify-school-email/",
        views.VerifySchoolEmailRequest.as_view(),
        name="verify-school-email",
    ),
    path(
        "verify-school-email/<str:token>/",
        views.ConfirmVerifySchoolEmail.as_view(),
        name="verify-school-email-token",
    ),
]
