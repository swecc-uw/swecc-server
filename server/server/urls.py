from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/user/', include('custom_auth.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('api/questions/', include("questions.urls")),
    path('api/members/', include("members.urls")),
    path('api/discord/', include("discord.urls")),
    path('api/interview/', include("interview.urls")),
    path('api/directory/', include('directory.urls')),
]
