import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)
KEY = "dashboard:summary"


def get():
    try:
        return cache.get(KEY)
    except Exception:
        logger.warning("Dashboard cache read failed; falling back to the database", exc_info=True)
        return None


def put(value) -> None:
    try:
        cache.set(KEY, value, settings.DASHBOARD_CACHE_TTL_SECONDS)
    except Exception:
        logger.warning("Dashboard cache write failed", exc_info=True)


def invalidate() -> None:
    try:
        cache.delete(KEY)
    except Exception:
        logger.warning("Dashboard cache invalidation failed", exc_info=True)
