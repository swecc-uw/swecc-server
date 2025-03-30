from django.urls import path

from . import views

urlpatterns = [
    path("upload/", views.ResumeUploadView.as_view(), name="resume-upload"),
]
