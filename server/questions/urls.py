from django.urls import path

from . import views

urlpatterns = [
    path(
        "topics/", views.QuestionTopicListCreateView.as_view(), name="topic-list-create"
    ),
    path(
        "topics/<uuid:topic_id>/",
        views.QuestionTopicUpdateView.as_view(),
        name="topic-update",
    ),
    path(
        "<str:type>/<uuid:question_id>/",
        views.QuestionDetailView.as_view(),
        name="question-detail",
    ),
    path("<str:type>/", views.QuestionCreateView.as_view(), name="question-create"),
    path("<str:type>/all/", views.QuestionListView.as_view(), name="question-list"),
    path(
        "<str:type>/queue/",
        views.QuestionQueueUpdateView.as_view(),
        name="question_queue",
    ),
]
