from celery import shared_task

from .overdue import run_overdue_check


@shared_task(
    name="service_requests.tasks.check_overdue",
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def check_overdue() -> dict:
    result = run_overdue_check()
    return {"marked": result.marked, "cleared": result.cleared, "durationMs": result.duration_ms}
