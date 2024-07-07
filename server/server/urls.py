from django.contrib import admin
from django.urls import path, include
from custom_auth.views import CreateUserView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView    

urlpatterns = [
    path('api/user/register/', CreateUserView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='get_token'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api-auth/', include('rest_framework.urls')),
    path('api/questions/', include("questions.urls")),
    path('api/members/', include("members.urls")),
    path('api/interview/', include("interview.urls")),
    path('api/directory/', include('directory.urls')),
]
