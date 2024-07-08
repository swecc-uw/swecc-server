from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.AuthKeyCreateView.as_view(), name='authkey-create'),
    path('list/', views.AuthKeyListView.as_view(), name='authkey-detail'),
    path('<uuid:pk>/', views.AuthKeyDetailView.as_view(), name='authkey-detail'),
]