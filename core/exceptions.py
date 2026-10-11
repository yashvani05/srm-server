import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response

from .responses import error_body

logger = logging.getLogger(__name__)


class Conflict(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict"


class ServiceUnavailable(exceptions.APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Service temporarily unavailable"


def _flatten(detail, prefix: str = ""):
    if isinstance(detail, dict):
        for key, value in detail.items():
            yield from _flatten(value, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(detail, list):
        for item in detail:
            yield from _flatten(item, prefix)
    else:
        yield (prefix or "body", str(detail))


def api_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied()

    from rest_framework.views import exception_handler

    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled error", exc_info=exc)
        return Response(error_body("Internal server error"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if isinstance(exc, exceptions.ValidationError):
        errors = [{"field": f if f != "non_field_errors" else "body", "message": m} for f, m in _flatten(exc.detail)]
        body = error_body("Validation failed", errors)
    elif isinstance(exc, exceptions.ParseError):
        body = error_body("Malformed JSON in request body")
    elif isinstance(exc, exceptions.NotAuthenticated):
        body = error_body("Authentication required")
    elif isinstance(exc, exceptions.Throttled):
        body = error_body("Too many login attempts. Please try again later.")
    elif isinstance(exc, exceptions.PermissionDenied):
        message = str(exc.detail)
        default = str(exceptions.PermissionDenied.default_detail)
        body = error_body("You do not have permission to perform this action" if message == default else message)
    elif isinstance(exc, exceptions.NotFound) and str(exc.detail) == str(exceptions.NotFound.default_detail):
        body = error_body("Resource not found")
    elif isinstance(exc, exceptions.APIException):
        body = error_body(str(exc.detail))
    else:
        body = error_body("Request failed")
    if isinstance(exc, (exceptions.AuthenticationFailed, exceptions.NotAuthenticated)):
        response.status_code = status.HTTP_401_UNAUTHORIZED
    response.data = body
    return response
