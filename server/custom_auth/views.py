import json
from django.contrib.auth import authenticate, login, logout
from rest_framework import generics, views
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import JsonResponse
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.middleware.csrf import get_token
from django.views.decorators.http import require_POST
from members.models import User
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

def get_csrf(request):
    response = JsonResponse({'detail': 'CSRF cookie set'})
    response['X-CSRFToken'] = get_token(request)
    return response

@require_POST
def login_view(request):
    data = json.loads(request.body)
    username = data.get('username').strip()
    password = data.get('password')
    
    if username is None or password is None:
        logger.error('Error logging in: username or password not provided')
        return JsonResponse({'detail': 'Please provide username and password.'}, status=400)
    
    user = authenticate(request, username=username, password=password)

    if user is None:
        logger.error('Error logging in: invalid credentials')
        return JsonResponse({'detail': 'Invalid credentials.'}, status=400)

    login(request, user)

    logger.info(f'User {username} logged in')
    return JsonResponse({'detail': 'Successfully logged in.'})


@require_POST
def register_view(request):
    data = json.loads(request.body)
    username = data.get('username').strip()
    password = data.get('password').strip()
    discord_username = data.get('discord_username')

    if not username or not password or not discord_username:
        logger.error('Error registering: username, password, or discord username not provided')
        return JsonResponse({'detail': 'Please provide username, password, and discord username.'}, status=400)

    try:
        with transaction.atomic():
            if User.objects.filter(username__iexact=username).exists():
                logger.error('Error registering: username already exists')
                return JsonResponse({'detail': 'Username already exists.'}, status=400)
            if User.objects.filter(discord_username__iexact=discord_username).exists():
                logger.error('Error registering: discord username already exists')
                return JsonResponse({'detail': 'Discord username already exists.'}, status=400)
            user = User.objects.create_user(username=username, password=password, discord_username=discord_username)
            
            logger.info(f'User {username} registered')
            return JsonResponse({'detail': 'Successfully registered.', 'id': user.id}, status=201)

    except Exception as e:
        logger.error(f'Error registering: {str(e)}')
        return JsonResponse({'detail': 'An error occurred during registration.', 'error': str(e)}, status=500)


def logout_view(request):
    if not request.user.is_authenticated:
        logger.error('Error logging out: user not logged in')
        return JsonResponse({'detail': 'You\'re not logged in.'}, status=400)

    logout(request)
    logger.info(f'User {request.user.username} logged out')
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
# class DiscordVerificationView(views.APIView):
#     authentication_classes = [SessionAuthentication, BasicAuthentication]
#     permission_classes = [AllowAny]

#     @staticmethod
#     def get(request, id, format=None):
#         try:
#             user = User.objects.get(id=id)
#             member = Member.objects.get(user=user)
#             return JsonResponse({'verified': bool(member.discord_id)})
#         except Exception as e:
#             if type(e) == User.DoesNotExist or type(e) == Member.DoesNotExist:
#                 return JsonResponse({'detail': 'User not found.'}, status=404)
#             return JsonResponse({'detail': 'An error occurred.'}, status=500)


