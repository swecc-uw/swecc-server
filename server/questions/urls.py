from django.urls import path
from . import views

urlpatterns = [
    path('topics/', views.QuestionTopicListView.as_view(), name='question-topics'),
    path('<str:type>/<uuid:question_id>/', views.QuestionDetailView.as_view(), name='question-detail'),
    path('<str:type>/', views.QuestionCreateView.as_view(), name='question-create'),
    path('<str:type>/all/', views.QuestionListView.as_view(), name='question-list'),
]