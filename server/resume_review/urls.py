from django.urls import path

from server.settings import DJANGO_DEBUG

from . import views

urlpatterns = [
    path("upload/", views.ResumeUploadView.as_view(), name="resume-upload"),
    path("", views.ResumeListView.as_view(), name="resume-list"),
]

if DJANGO_DEBUG:
    urlpatterns += [
        path(
            "publish-to-review/",
            views.DevPublishToReview.as_view(),
            name="dev-publish-to-review-resume",
        ),
    ]
