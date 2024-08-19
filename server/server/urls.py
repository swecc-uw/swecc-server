from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('auth/', include('custom_auth.urls')),
    path('questions/', include("questions.urls")),
    path('members/', include("members.urls")),
    path('interview/', include("interview.urls")),
    path('directory/', include('directory.urls')),
]
