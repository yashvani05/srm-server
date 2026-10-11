from django.db.models import Count, Q

from service_requests.models import ServiceRequest, SystemState
from service_requests.overdue import STATE_KEY

S = ServiceRequest.Status


def build_summary() -> dict:
    counts = ServiceRequest.objects.aggregate(
        totalRequests=Count("id"),
        openRequests=Count("id", filter=Q(status=S.OPEN)),
        inProgressRequests=Count("id", filter=Q(status=S.IN_PROGRESS)),
        resolvedRequests=Count("id", filter=Q(status=S.RESOLVED)),
        highPriorityRequests=Count("id", filter=Q(priority=ServiceRequest.Priority.HIGH)),
        overdueRequests=Count("id", filter=Q(overdue=True)),
    )
    return counts


def last_overdue_check_at():
    state = SystemState.objects.filter(key=STATE_KEY).first()
    return state.updated_at if state else None
