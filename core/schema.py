from functools import lru_cache

from rest_framework import serializers


class FieldErrorSerializer(serializers.Serializer):
    field = serializers.CharField(required=False)
    message = serializers.CharField()


class ErrorEnvelopeSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    errors = FieldErrorSerializer(many=True)


class PaginationSerializer(serializers.Serializer):
    page = serializers.IntegerField()
    limit = serializers.IntegerField()
    totalItems = serializers.IntegerField()
    totalPages = serializers.IntegerField()


@lru_cache(maxsize=None)
def envelope(name: str, data_serializer=None, many: bool = False):
    data = data_serializer(many=many) if data_serializer else serializers.JSONField(allow_null=True)
    return type(name, (serializers.Serializer,), {
        "success": serializers.BooleanField(default=True),
        "message": serializers.CharField(),
        "data": data,
    })


ERRORS = {
    400: ErrorEnvelopeSerializer,
    401: ErrorEnvelopeSerializer,
    403: ErrorEnvelopeSerializer,
    404: ErrorEnvelopeSerializer,
}
