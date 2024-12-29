from django.urls import path
from . import views

urlpatterns = [
    path(
        "message/",
        views.InjestMessageEventView.as_view(),
        name="injest-message-event",
    ),
]