from django.urls import path

from . import views

urlpatterns = [
    path(
        "users/<int:user_id>/",
        views.GetReportByUserID.as_view(),
        name="get-report-by-user-id",
    ),
    path("all/", views.GetAllReports.as_view(), name="get-all-reports"),
    path("<uuid:report_id>/", views.GetReportByID.as_view(), name="get-report-by-id"),
    path(
        "<uuid:report_id>/assign/",
        views.AssignReportToAdmin.as_view(),
        name="assign-report-to-admin",
    ),
    path("", views.CreateReport.as_view(), name="create-report"),
    path(
        "<uuid:report_id>/status/",
        views.UpdateReportStatus.as_view(),
        name="update-report-status",
    ),
]
