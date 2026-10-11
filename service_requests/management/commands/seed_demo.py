import os
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from accounts.roles import ADMIN, EMPLOYEE
from dashboard import cache
from service_requests.models import ServiceRequest

SAMPLES = [
    ("Laptop screen flickers on battery", "IT", "HIGH", "OPEN", 30, "employee", "The screen flickers whenever the laptop is unplugged. Started after the last Windows update."),
    ("VPN disconnects every few minutes", "IT", "HIGH", "IN_PROGRESS", 52, "employee", "Working from home, the VPN drops roughly every 5 minutes and I have to reconnect manually."),
    ("Request access to the shared finance drive", "IT", "MEDIUM", "OPEN", 5, "employee", "I have moved to the finance team and need read access to the shared finance drive."),
    ("Replace broken chair in meeting room 3", "MAINTENANCE", "LOW", "OPEN", 48, "employee", "One of the chairs in meeting room 3 has a broken gas lift and sinks when sat on."),
    ("Air conditioning too cold on 2nd floor", "MAINTENANCE", "MEDIUM", "IN_PROGRESS", 9, "employee", "The east side of the 2nd floor is uncomfortably cold in the mornings."),
    ("Leaking tap in the kitchen", "MAINTENANCE", "HIGH", "RESOLVED", 96, "admin", "The mixer tap in the ground floor kitchen drips constantly."),
    ("Order extra monitors for new starters", "GENERAL", "MEDIUM", "IN_PROGRESS", 72, "admin", "Three new starters join next month and each needs a second monitor."),
    ("Update the office visitor policy", "GENERAL", "LOW", "OPEN", 1, "admin", "The visitor policy on the intranet still references the old reception desk process."),
    ("Printer on 1st floor jams constantly", "IT", "MEDIUM", "RESOLVED", 144, "employee", "Paper jams on nearly every job. Tray 2 seems to be the culprit."),
    ("Request a standing desk", "GENERAL", "LOW", "RESOLVED", 192, "employee", "Ergonomic assessment recommended a standing desk."),
    ("Wi-Fi drops in the north corridor", "IT", "HIGH", "OPEN", 26, "admin", "Dead spot near the north corridor stairwell; video calls cut out."),
    ("Light fitting flickering in reception", "MAINTENANCE", "LOW", "OPEN", 20, "employee", "The downlight above the reception desk flickers intermittently."),
]


class Command(BaseCommand):
    help = "Create the demo admin + employee users and 12 sample requests (safe to run repeatedly)."

    def handle(self, *args, **options):
        env = os.environ.get
        users = {
            "admin": self._user(env("SEED_ADMIN_EMAIL", "admin@company.com"), "Admin User", env("SEED_ADMIN_PASSWORD", "Admin@12345"), ADMIN),
            "employee": self._user(env("SEED_EMPLOYEE_EMAIL", "employee@company.com"), "Employee User", env("SEED_EMPLOYEE_PASSWORD", "Employee@12345"), EMPLOYEE),
        }
        now, created = timezone.now(), 0
        for title, category, priority, status, hours, owner, description in SAMPLES:
            if ServiceRequest.objects.filter(title=title).exists():
                continue
            when = now - timedelta(hours=hours)
            is_overdue = status != "RESOLVED" and hours > 24
            ServiceRequest.objects.create(
                title=title, description=description, category=category, priority=priority, status=status,
                created_by=users[owner], created_at=when, status_changed_at=when,
                overdue=is_overdue, overdue_at=now if is_overdue else None,
            )
            created += 1
        cache.invalidate()
        self.stdout.write(self.style.SUCCESS(f"Seed complete: {created} new request(s)."))

    def _user(self, email, name, password, role):
        user = User.objects.filter(email__iexact=email).first()
        return user or User.objects.create_user(email=email.lower(), name=name, password=password, role=role)
