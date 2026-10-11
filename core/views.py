import hmac
import time

from django.db import connection
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework import serializers

from .responses import error_body, success
from .schema import envelope

STARTED_AT = time.time()


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    cache = serializers.CharField(help_text="Redis cache status")
    uptime = serializers.FloatField(help_text="Seconds since the process started")


class HealthView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(tags=["System"], summary="Health check", description="Confirms the API is up and can reach PostgreSQL.",
                   responses={200: envelope("HealthResponse", HealthSerializer)}, auth=[])
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        try:
            cache.set("health:ping", 1, timeout=10)
            cache_status = "ok"
        except Exception as exc:
            cache_status = f"error: {type(exc).__name__}"
        return success("Service is healthy", {"status": "ok", "cache": cache_status, "uptime": time.time() - STARTED_AT})


class CronOverdueView(APIView):
    """Run the overdue check on demand; called by Vercel Cron (which sends `Authorization: Bearer $CRON_SECRET`)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(exclude=True)
    def get(self, request):
        secret = settings.CRON_SECRET
        if not secret or not hmac.compare_digest(request.headers.get("Authorization", ""), f"Bearer {secret}"):
            return JsonResponse(error_body("Unauthorized"), status=401)
        from service_requests.overdue import run_overdue_check

        result = run_overdue_check()
        return success("Overdue check complete", {"marked": result.marked, "cleared": result.cleared, "durationMs": result.duration_ms})


def root(request):
    return JsonResponse({"success": True, "message": "Service Request Management API", "data": {"health": "/api/v1/health", "docs": "/api-docs/"}})


def api_not_found(request, *args, **kwargs):
    return JsonResponse(error_body(f"Route not found: {request.method} {request.get_full_path()}"), status=404)


def server_error(request):
    return JsonResponse(error_body("Internal server error"), status=500)
