from django.urls import path
from . import views

urlpatterns = [
    path('csrf/', views.get_csrf, name='api-csrf'),
    path('login/', views.login_view, name='api-login'),
    path('logout/', views.logout_view, name='api-logout'),
    path('session/', views.SessionView.as_view(), name='api-session'),  
    path('whoami/', views.WhoAmIView.as_view(), name='api-whoami'), 
    path('register/', views.register_view, name='register'),
    path('register/ssflow/', views.RegisterWithApiKeyView.as_view(), name='register-ssflow'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('jwt/', views.CreateTokenView.as_view(), name='api-jwt'),
    # path('<int:id>/verified/', views.DiscordVerificationView.as_view(), name='api-verified'),
]