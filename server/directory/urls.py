from django.urls import path
from .views import MemberDirectorySearchView, MemberDirectoryView

urlpatterns = [
    path('search/', MemberDirectorySearchView.as_view(), name='member-directory-search'),
    path('<int:id>/', MemberDirectoryView.as_view(), name='member-directory'),
]