from rest_framework import serializers

from .models import ServiceRequest


class CreatedBySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


class ServiceRequestSerializer(serializers.ModelSerializer):

    isOverdue = serializers.BooleanField(source="overdue", read_only=True, help_text="OPEN/IN_PROGRESS for more than 24h in the current status")
    statusChangedAt = serializers.DateTimeField(source="status_changed_at", read_only=True, help_text="When the current status began (the overdue clock)")
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    createdBy = CreatedBySerializer(source="created_by", read_only=True)

    class Meta:
        model = ServiceRequest
        fields = ["id", "title", "description", "category", "priority", "status", "isOverdue", "statusChangedAt", "createdAt", "updatedAt", "createdBy"]


class RequestFieldsSerializer(serializers.Serializer):

    title = serializers.CharField(min_length=3, max_length=150)
    description = serializers.CharField(max_length=5000)
    category = serializers.ChoiceField(choices=ServiceRequest.Category.choices)
    priority = serializers.ChoiceField(choices=ServiceRequest.Priority.choices, required=False, default=ServiceRequest.Priority.MEDIUM)


class StrictRequestFieldsSerializer(RequestFieldsSerializer):

    status = serializers.CharField(required=False, write_only=True)

    def validate_status(self, value):
        raise serializers.ValidationError("status cannot be set here; use PATCH /requests/:id/status")

    def validate(self, attrs):
        if self.partial and not attrs:
            raise serializers.ValidationError("At least one field is required")
        return attrs


class StatusInputSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ServiceRequest.Status.choices)


class ListQuerySerializer(serializers.Serializer):

    status = serializers.ChoiceField(choices=ServiceRequest.Status.choices, required=False)
    priority = serializers.ChoiceField(choices=ServiceRequest.Priority.choices, required=False)
    overdue = serializers.BooleanField(required=False)
    page = serializers.IntegerField(min_value=1, default=1)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=10)

    def to_internal_value(self, data):
        data = data.copy()
        for key in ("status", "priority"):
            if key in data:
                data[key] = str(data[key]).upper()
        return super().to_internal_value(data)


class PaginatedRequestsSerializer(serializers.Serializer):
    items = ServiceRequestSerializer(many=True)
    pagination = serializers.DictField(child=serializers.IntegerField())
