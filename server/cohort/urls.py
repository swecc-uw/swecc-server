from django.urls import path
from . import views

urlpatterns = [
    path("", views.CohortListCreateView.as_view(), name="cohort-list-create"),
    path(
        "<int:pk>/",
        views.CohortRetrieveUpdateDestroyView.as_view(),
        name="cohort-detail",
    ),
]
