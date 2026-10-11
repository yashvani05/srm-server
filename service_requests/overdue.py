import logging
import time
from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.db.models import DateTimeField, ExpressionWrapper, Q
from django.db.models.functions import Now

from dashboard import cache as dashboard_cache

from .constants import OVERDUE_AFTER_HOURS
from .models import ServiceRequest, SystemState

logger = logging.getLogger(__name__)

STATE_KEY = "overdue_check.last_success_at"


def qualifies_as_overdue() -> Q:
    cutoff = ExpressionWrapper(Now() - timedelta(hours=OVERDUE_AFTER_HOURS), output_field=DateTimeField())
    return Q(status__in=[ServiceRequest.Status.OPEN, ServiceRequest.Status.IN_PROGRESS], status_changed_at__lt=cutoff)


@dataclass
class OverdueCheckResult:
    marked: int
    cleared: int
    duration_ms: int


def run_overdue_check() -> OverdueCheckResult:
    started = time.monotonic()
    with transaction.atomic():
        marked = ServiceRequest.objects.filter(overdue=False).filter(qualifies_as_overdue()).update(overdue=True, overdue_at=Now())
        cleared = ServiceRequest.objects.filter(overdue=True).exclude(qualifies_as_overdue()).update(overdue=False, overdue_at=None)
        SystemState.objects.update_or_create(key=STATE_KEY, defaults={"value": "ok", "updated_at": Now()})

    if marked or cleared:
        dashboard_cache.invalidate()

    result = OverdueCheckResult(marked=marked, cleared=cleared, duration_ms=int((time.monotonic() - started) * 1000))
    logger.info("Overdue check finished: marked=%s cleared=%s in %sms", result.marked, result.cleared, result.duration_ms)
    return result
