import time

from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from core.exceptions import Conflict
from core.responses import success
from core.schema import ERRORS, envelope

from . import denylist
from .jwt import issue_token
from .models import User
from .serializers import AuthResultSerializer, CurrentUserSerializer, LoginSerializer, RegisterSerializer, UserSerializer
from .throttles import LoginThrottle

_DUMMY_HASH = None


def _dummy_hash() -> str:
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = make_password("not-a-real-password")
    return _DUMMY_HASH


def _auth_result(user: User) -> dict:
    return {"token": issue_token(user), "user": UserSerializer(user).data}


class RegisterView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"], summary="Register an account", auth=[], request=RegisterSerializer,
        description="Creates a new account with the EMPLOYEE role (any `role` in the body is ignored) and signs it in.",
        responses={201: envelope("RegisterResponse", AuthResultSerializer), 400: ERRORS[400], 409: ERRORS[400]},
    )
    def post(self, request):
        data = RegisterSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        email = data.validated_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise Conflict("An account with this email already exists")
        try:
            user = User.objects.create_user(email=email, name=data.validated_data["name"], password=data.validated_data["password"])
        except IntegrityError:
            raise Conflict("An account with this email already exists")
        return success("Registration successful", _auth_result(user), status=201)


class LoginView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @extend_schema(
        tags=["Auth"], summary="Log in", auth=[], request=LoginSerializer,
        description="Returns a JWT. Rate limited per IP (default 10 attempts per 15 minutes, `LOGIN_RATE_LIMIT_MAX`).",
        responses={200: envelope("LoginResponse", AuthResultSerializer), 400: ERRORS[400], 401: ERRORS[401], 429: ERRORS[400]},
    )
    def post(self, request):
        data = LoginSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=data.validated_data["email"].strip()).first()
        password_ok = check_password(data.validated_data["password"], user.password if user else _dummy_hash())
        if not user or not user.is_active or not password_ok:
            raise AuthenticationFailed("Invalid email or password")
        return success("Login successful", _auth_result(user))


class LogoutView(APIView):
    @extend_schema(
        tags=["Auth"], summary="Log out", request=None,
        description="Revokes the current token: its id is stored in Redis until it would have expired, so it cannot be reused.",
        responses={200: envelope("LogoutResponse"), 401: ERRORS[401], 503: ERRORS[400]},
    )
    def post(self, request):
        denylist.deny(request.auth["jti"], request.auth["exp"])
        return success("Logged out successfully", None)


class MeView(APIView):
    @extend_schema(
        tags=["Auth"], summary="Current user",
        description="The signed-in user with their role and permission names (used by the UI to show or hide controls).",
        responses={200: envelope("CurrentUserResponse", CurrentUserSerializer), 401: ERRORS[401]},
    )
    def get(self, request):
        return success("Current user fetched successfully", {"user": UserSerializer(request.user).data})
