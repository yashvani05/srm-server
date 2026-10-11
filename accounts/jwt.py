import time
import uuid

import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

ALGORITHM = "HS256"


def issue_token(user) -> str:
    now = int(time.time())
    payload = {"sub": str(user.pk), "role": user.role, "jti": str(uuid.uuid4()), "iat": now, "exp": now + settings.JWT_EXPIRES_SECONDS}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM], options={"require": ["exp", "sub", "jti"]})
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token")
