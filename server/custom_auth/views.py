import json
from django.contrib.auth import authenticate, login, logout, models
from rest_framework import generics, views
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import JsonResponse
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.middleware.csrf import get_token
from django.views.decorators.http import require_POST
from members.models import Member
from django.contrib.auth.models import User
from django.db import transaction

class CreateUserView(generics.CreateAPIView):
    queryset = models.User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

def get_csrf(request):
    response = JsonResponse({'detail': 'CSRF cookie set'})
    response['X-CSRFToken'] = get_token(request)
    return response

@require_POST
def login_view(request):
    data = json.loads(request.body)
    username = data.get('username').strip().lower()
    password = data.get('password').strip()
    
    if username is None or password is None:
            return JsonResponse({'detail': 'Please provide username and password.'}, status=400)
    
    user = authenticate(request, username=username, password=password)

    if user is not None:
        try:
            member = Member.objects.get(user=user)
            if not member.discord_id:
                logout(request)
                return JsonResponse({
                    "detail": "Your account does not have a Discord ID associated with it.",
                    "username": member.user.username
                }, status=403)

            login(request, user)
            return JsonResponse({'detail': 'Successfully logged in.'})

        except Member.DoesNotExist:
            logout(request)
            return JsonResponse({
                "detail": "Your account does not have a Discord ID associated with it.",
                "user_id": member.user.username
            }, status=403)

    return JsonResponse({'detail': 'Invalid credentials.'}, status=400)


@require_POST
def register_view(request):
    data = json.loads(request.body)
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()
    discord_username = data.get('discord_username', '').strip().lower()

    if not username or not password or not discord_username:
        return JsonResponse({'detail': 'Please provide username, password, and discord username.'}, status=400)

    try:
        with transaction.atomic():
            if User.objects.filter(username=username).exists():
                return JsonResponse({'detail': 'Username already exists.'}, status=400)
            if Member.objects.filter(discord_username=discord_username).exists():
                return JsonResponse({'detail': 'Discord username already exists.'}, status=400)
            user = User.objects.create_user(username=username, password=password)
            Member.objects.create(user=user, discord_username=discord_username)
            return JsonResponse({'detail': 'Successfully registered.', 'id': user.id}, status=201)

    except Exception as e:
        return JsonResponse({'detail': 'An error occurred during registration.', 'error': str(e)}, status=500)


def logout_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'You\'re not logged in.'}, status=400)

    logout(request)
    return JsonResponse({'detail': 'Successfully logged out.'})


class SessionView(views.APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request, format=None):
        return JsonResponse({'isAuthenticated': True})


class WhoAmIView(views.APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request, format=None):
        return JsonResponse({'username': request.user.username})

# endpoint for checking if a user's account is verified through
# Discord. Essentially, if they have a Discord ID associated with
# their account. user does not need to be logged in to access this view
class DiscordVerificationView(views.APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    @staticmethod
    def get(request, id, format=None):
        try:
            user = User.objects.get(id=id)
            member = Member.objects.get(user=user)
            return JsonResponse({'verified': bool(member.discord_id)})
        except Exception as e:
            if type(e) == User.DoesNotExist or type(e) == Member.DoesNotExist:
                return JsonResponse({'detail': 'User not found.'}, status=404)
            return JsonResponse({'detail': 'An error occurred.'}, status=500)


