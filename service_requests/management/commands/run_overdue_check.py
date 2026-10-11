from django.core.management.base import BaseCommand

from service_requests.overdue import run_overdue_check


class Command(BaseCommand):
    help = "Run the overdue check once, right now (the same job Celery Beat schedules every minute)."

    def handle(self, *args, **options):
        r = run_overdue_check()
        self.stdout.write(f"marked={r.marked} cleared={r.cleared} in {r.duration_ms}ms")
