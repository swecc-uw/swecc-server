import json
import logging
import secrets
import time
from typing import Dict, Optional, Tuple

import jwt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_POST
from members.models import User
from members.permissions import IsApiKey
from rest_framework import generics, views
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated

from server.settings import JWT_SECRET

from .serializers import UserSerializer

logger = logging.getLogger(__name__)


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


def get_csrf(request):
    response = JsonResponse({"detail": "CSRF cookie set"})
    response["X-CSRFToken"] = get_token(request)
    return response


@require_POST
def login_view(request):
    data = json.loads(request.body)
    username = data.get("username").strip()
    password = data.get("password")

    if username is None or password is None:
        logger.error("Error logging in: username or password not provided")
        return JsonResponse(
            {"detail": "Please provide username and password."}, status=400
        )

    user = authenticate(request, username=username, password=password)

    if user is None:
        logger.error("Error logging in: invalid credentials")
        return JsonResponse({"detail": "Invalid credentials."}, status=400)

    login(request, user)

    logger.info("User %s logged in", username)
    return JsonResponse({"detail": "Successfully logged in."})


@require_POST
def password_reset_confirm(request, uidb64, token):
    data = json.loads(request.body)
    new_password = data.get("new_password", "").strip()

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return JsonResponse(
                {"detail": "Password has been reset successfully."}, status=200
            )
        else:
            return JsonResponse({"detail": "Invalid token."}, status=400)

    except (User.DoesNotExist, ValueError):
        return JsonResponse({"detail": "Invalid request."}, status=400)


def create_password_reset_creds(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return uid, token


def validate_user_data(
    data, include_password=True
) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    discord_username = data.get("discord_username", "").strip()

    required_fields = [
        "username",
        "email",
        "first_name",
        "last_name",
        "discord_username",
    ]
    if include_password:
        required_fields.append("password")

    field_values = {
        "username": username,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "discord_username": discord_username,
    }

    if include_password:
        field_values["password"] = data.get("password", "").strip()

    missing_fields = [field for field in required_fields if not field_values.get(field)]

    if missing_fields:
        missing_fields_str = ", ".join(missing_fields)
        return None, f"Please provide {missing_fields_str}."

    return field_values, None


def check_existing_user(field_values, source="registration"):
    username = field_values.get("username")
    email = field_values.get("email")
    discord_username = field_values.get("discord_username")

    if User.objects.filter(username__iexact=username).exists():
        logger.error(f"Error {source}: username already exists")
        return "Username already exists. Try logging in, or use `/reset_password` in the discord server to reset your password."

    existing_user_with_discord = User.objects.filter(
        discord_username__iexact=discord_username
    ).first()

    if existing_user_with_discord:
        logger.error(f"Error {source}: discord username already exists")
        return f"Discord username {discord_username} already exists, in use by user '{existing_user_with_discord.username}'. Try logging in, or use `/reset_password` in the discord server to reset your password."

    existing_user_with_email = User.objects.filter(email__iexact=email).first()
    if existing_user_with_email:
        logger.error(f"Error {source}: email already exists")
        return f"Email {email} already exists, in use by user '{existing_user_with_email.username}'. Try logging in, or use `/reset_password` in the discord server to reset your password."

    return None


@require_POST
def register_view(request):
    data = json.loads(request.body)

    field_values, error_message = validate_user_data(data)
    if error_message or not field_values:
        logger.error(f"Error registering: {error_message}")
        return JsonResponse({"detail": error_message}, status=400)

    try:
        with transaction.atomic():
            error = check_existing_user(field_values)
            if error:
                return JsonResponse({"detail": error}, status=400)

            user = User.objects.create_user(
                username=field_values["username"],
                email=field_values["email"],
                password=field_values["password"],
                discord_username=field_values["discord_username"],
                first_name=field_values["first_name"],
                last_name=field_values["last_name"],
            )

            logger.info("User %s registered", field_values["username"])
            return JsonResponse(
                {"detail": "Successfully registered.", "id": user.id}, status=201
            )

    except Exception as e:
        logger.error("Error registering: %s", str(e))
        return JsonResponse(
            {"detail": "An error occurred during registration.", "error": str(e)},
            status=500,
        )


def logout_view(request):
    if not request.user.is_authenticated:
        logger.error("Error logging out: user not logged in")
        return JsonResponse({"detail": "You're not logged in."}, status=400)

    username = request.user.username
    logout(request)
    logger.info("User %s logged out", username)
    return JsonResponse({"detail": "Successfully logged out."})


class SessionView(views.APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request, format=None):
        return JsonResponse({"isAuthenticated": True})


class WhoAmIView(views.APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request, format=None):
        return JsonResponse({"username": request.user.username})


class CreateTokenView(views.APIView):
    permission_classes = [IsAuthenticated | IsApiKey]

    @staticmethod
    def get(request, format=None):
        user_id, username = request.user.id, request.user.username
        groups = request.user.groups.all()
        is_api_key = False

        try:
            is_api_key = IsApiKey().has_permission(request, None)
        except Exception:
            pass

        groups = [group.name for group in groups] + ["is_authenticated"]
        if is_api_key:
            groups.append("api_key")

        hour = 60 * 60
        payload = {
            "user_id": user_id,
            "username": username,
            "groups": groups,
            "exp": int(time.time()) + hour,
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        return JsonResponse({"token": token.decode()})


class RegisterWithApiKeyView(views.APIView):
    permission_classes = [IsApiKey]

    @staticmethod
    def post(request):
        data = json.loads(request.body)

        field_values, error_message = validate_user_data(data, include_password=False)
        if error_message:
            logger.error(f"Error registering with API: {error_message}")
            return JsonResponse({"detail": error_message}, status=400)

        try:
            with transaction.atomic():
                error = check_existing_user(field_values, source="registering with API")
                if error:
                    return JsonResponse({"detail": error}, status=400)

                temp_password = secrets.token_urlsafe(32)
                field_values["password"] = temp_password

                user = User.objects.create_user(
                    username=field_values["username"],
                    email=field_values["email"],
                    password=temp_password,
                    discord_username=field_values["discord_username"],
                    first_name=field_values["first_name"],
                    last_name=field_values["last_name"],
                )

                uid, token = create_password_reset_creds(user)
                reset_url = f"https://engagement.swecc.org/#/password-reset-confirm/{uid}/{token}"

                logger.info("User %s registered via API", field_values["username"])
                return JsonResponse(
                    {
                        "detail": "Successfully registered.",
                        "id": user.id,
                        "reset_password_url": reset_url,
                    },
                    status=201,
                )

        except Exception as e:
            logger.error("Error registering with API: %s", str(e))
            return JsonResponse(
                {"detail": "An error occurred during registration.", "error": str(e)},
                status=500,
            )
