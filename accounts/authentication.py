from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .denylist import is_denied
from .jwt import decode_token
from .models import User


class JWTAuthentication(BaseAuthentication):

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None

        claims = decode_token(header[len("Bearer "):].strip())
        if is_denied(claims["jti"]):
            raise AuthenticationFailed("Token has been revoked")

        user = User.objects.filter(pk=claims["sub"], is_active=True).first()
        if user is None:
            raise AuthenticationFailed("Invalid token")
        return user, claims

    def authenticate_header(self, request):
        return "Bearer"
