import time

from django.db import connection
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
    uptime = serializers.FloatField(help_text="Seconds since the process started")


class HealthView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(tags=["System"], summary="Health check", description="Confirms the API is up and can reach PostgreSQL.",
                   responses={200: envelope("HealthResponse", HealthSerializer)}, auth=[])
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return success("Service is healthy", {"status": "ok", "uptime": time.time() - STARTED_AT})


def api_not_found(request, *args, **kwargs):
    return JsonResponse(error_body(f"Route not found: {request.method} {request.get_full_path()}"), status=404)


def server_error(request):
    return JsonResponse(error_body("Internal server error"), status=500)
