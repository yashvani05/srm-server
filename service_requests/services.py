from django.db.models.functions import Now
from rest_framework.exceptions import NotFound, PermissionDenied

from accounts import roles
from dashboard import cache as dashboard_cache

from .models import ServiceRequest

Status = ServiceRequest.Status


def _is_admin(user) -> bool:
    return user.role == roles.ADMIN


def _visible_to(user):
    queryset = ServiceRequest.objects.select_related("created_by")
    return queryset if _is_admin(user) else queryset.filter(created_by=user)


def list_requests(user, *, status=None, priority=None, overdue=None, page=1, limit=10):
    queryset = _visible_to(user)
    if status:
        queryset = queryset.filter(status=status)
    if priority:
        queryset = queryset.filter(priority=priority)
    if overdue:
        queryset = queryset.filter(overdue=True)
    queryset = queryset.order_by("-created_at", "-id")
    total = queryset.count()
    offset = (page - 1) * limit
    return list(queryset[offset:offset + limit]), total


def get_request(user, pk) -> ServiceRequest:
    request = _visible_to(user).filter(pk=pk).first()
    if request is None:
        raise NotFound("Service request not found")
    return request


def create_request(user, data: dict) -> ServiceRequest:
    request = ServiceRequest.objects.create(created_by=user, **data)
    dashboard_cache.invalidate()
    return ServiceRequest.objects.select_related("created_by").get(pk=request.pk)


def update_request(user, pk, data: dict) -> ServiceRequest:
    request = get_request(user, pk)
    if not _is_admin(user) and request.status != Status.OPEN:
        raise PermissionDenied("Only open requests can be edited")
    for field, value in data.items():
        setattr(request, field, value)
    request.save(update_fields=[*data.keys(), "updated_at"])
    dashboard_cache.invalidate()
    return request


def change_status(user, pk, status: str) -> ServiceRequest:
    request = get_request(user, pk)
    if request.status == status:
        return request
    request.status = status
    request.status_changed_at = Now()
    request.overdue = False
    request.overdue_at = None
    request.save(update_fields=["status", "status_changed_at", "overdue", "overdue_at", "updated_at"])
    request.refresh_from_db()
    dashboard_cache.invalidate()
    return request


def delete_request(user, pk) -> None:
    get_request(user, pk).delete()
    dashboard_cache.invalidate()
