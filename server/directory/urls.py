from django.urls import path
from .views import MemberDirectoryView

urlpatterns = [
    path('search/', MemberDirectoryView.as_view(), name='member-directory-search'),
]