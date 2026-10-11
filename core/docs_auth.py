import base64
import hashlib
import hmac
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

MAX_FAILED_ATTEMPTS = 20
WINDOW_SECONDS = 15 * 60


def _same(a: str, b: str) -> bool:
    return hmac.compare_digest(hashlib.sha256(a.encode()).digest(), hashlib.sha256(b.encode()).digest())


def basic_auth_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        ip = request.META.get("REMOTE_ADDR", "")
        counter = f"docs-auth-failures:{ip}"
        header = request.META.get("HTTP_AUTHORIZATION", "")

        try:
            if (cache.get(counter) or 0) >= MAX_FAILED_ATTEMPTS:
                return HttpResponse("Too many failed attempts. Please try again later.", status=429, content_type="text/plain")
        except Exception:
            pass

        if header.startswith("Basic "):
            try:
                user, _, password = base64.b64decode(header[6:]).decode().partition(":")
            except Exception:
                user = password = ""
            ok_user, ok_pass = _same(user, settings.SWAGGER_USER), _same(password, settings.SWAGGER_PASS)
            if ok_user and ok_pass:
                return view(request, *args, **kwargs)
            try:
                cache.set(counter, (cache.get(counter) or 0) + 1, WINDOW_SECONDS)
            except Exception:
                pass

        response = HttpResponse("Authentication required", status=401, content_type="text/plain")
        response["WWW-Authenticate"] = 'Basic realm="API Documentation", charset="UTF-8"'
        return response

    return wrapper
