from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from accounts.permissions import require_permission
from core.responses import success
from core.schema import ERRORS, envelope

from . import services
from .serializers import (ListQuerySerializer, PaginatedRequestsSerializer, RequestFieldsSerializer, ServiceRequestSerializer,
                          StatusInputSerializer, StrictRequestFieldsSerializer)

import uuid

Item = envelope("ServiceRequestEnvelope", ServiceRequestSerializer)
Page = envelope("ServiceRequestPageEnvelope", PaginatedRequestsSerializer)
Empty = envelope("EmptyEnvelope", None)


def _check_id(pk: str) -> str:
    try:
        return str(uuid.UUID(pk))
    except ValueError:
        raise ValidationError({"id": ["id must be a valid UUID"]})


def _body(serializer_class, data, partial=False) -> dict:
    serializer = serializer_class(data=data, partial=partial)
    serializer.is_valid(raise_exception=True)
    return dict(serializer.validated_data)


class RequestCollectionView(APIView):
    def get_permissions(self):
        return [require_permission("requests.create" if self.request.method == "POST" else "requests.read")()]

    @extend_schema(
        tags=["Service Requests"], summary="List service requests", operation_id="requests_list",
        parameters=[OpenApiParameter("status", str), OpenApiParameter("priority", str), OpenApiParameter("overdue", bool),
                    OpenApiParameter("page", int), OpenApiParameter("limit", int)],
        responses={200: Page, 400: ERRORS[400], 401: ERRORS[401], 403: ERRORS[403]},
    )
    def get(self, request):
        query = ListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        q = query.validated_data
        items, total = services.list_requests(request.user, status=q.get("status"), priority=q.get("priority"),
                                              overdue=q.get("overdue"), page=q["page"], limit=q["limit"])
        pages = -(-total // q["limit"])
        return success("Service requests retrieved", {
            "items": ServiceRequestSerializer(items, many=True).data,
            "pagination": {"page": q["page"], "limit": q["limit"], "totalItems": total, "totalPages": pages},
        })

    @extend_schema(tags=["Service Requests"], summary="Create a service request", request=RequestFieldsSerializer,
                   responses={201: Item, 400: ERRORS[400], 401: ERRORS[401], 403: ERRORS[403]})
    def post(self, request):
        data = _body(StrictRequestFieldsSerializer, request.data)
        created = services.create_request(request.user, data)
        return success("Service request created", ServiceRequestSerializer(created).data, status=201)


class RequestDetailView(APIView):
    def get_permissions(self):
        perm = {"GET": "requests.read", "PATCH": "requests.update", "DELETE": "requests.delete"}[self.request.method]
        return [require_permission(perm)()]

    @extend_schema(tags=["Service Requests"], summary="Get one service request",
                   responses={200: Item, 400: ERRORS[400], 401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404]})
    def get(self, request, pk):
        return success("Service request retrieved", ServiceRequestSerializer(services.get_request(request.user, _check_id(pk))).data)

    @extend_schema(tags=["Service Requests"], summary="Edit a service request", request=RequestFieldsSerializer,
                   responses={200: Item, 400: ERRORS[400], 401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404]})
    def patch(self, request, pk):
        pk = _check_id(pk)
        data = _body(StrictRequestFieldsSerializer, request.data, partial=True)
        if "priority" not in request.data:
            data.pop("priority", None)
        return success("Service request updated", ServiceRequestSerializer(services.update_request(request.user, pk, data)).data)

    @extend_schema(tags=["Service Requests"], summary="Delete a service request (admin only)",
                   responses={200: Empty, 400: ERRORS[400], 401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404]})
    def delete(self, request, pk):
        services.delete_request(request.user, _check_id(pk))
        return success("Service request deleted")


class RequestStatusView(APIView):
    def get_permissions(self):
        return [require_permission("requests.status.update")()]

    @extend_schema(tags=["Service Requests"], summary="Change status (admin only)", request=StatusInputSerializer,
                   responses={200: Item, 400: ERRORS[400], 401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404]})
    def patch(self, request, pk):
        pk = _check_id(pk)
        data = _body(StatusInputSerializer, request.data)
        return success("Service request status updated", ServiceRequestSerializer(services.change_status(request.user, pk, data["status"])).data)
