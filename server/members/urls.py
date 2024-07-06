from django.urls import path
from . import views

urlpatterns = [
    path('', views.MembersList.as_view(), name='members-list'),
    path(
        '<int:member_id>/', 
        views.MemberRetrieveUpdateDestroy.as_view(), 
        name='member-retrieve-update-destroy'
        ),
    path('profile/', views.AuthenticatedMemberProfile.as_view(), name='authenticated-profile'),

]