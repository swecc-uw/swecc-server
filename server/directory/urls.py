from django.urls import path
from .views import (
    MemberDirectorySearchView,
    MemberDirectoryView,
    RecommendedMembersView,
)

urlpatterns = [
    path(
        "search/", MemberDirectorySearchView.as_view(), name="member-directory-search"
    ),
    path("recommended/", RecommendedMembersView.as_view(), name="recommended-members"),
    path("<int:id>/", MemberDirectoryView.as_view(), name="member-directory"),
]
