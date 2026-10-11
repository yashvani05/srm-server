import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ServiceRequest(models.Model):

    class Category(models.TextChoices):
        IT = "IT", "IT"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        GENERAL = "GENERAL", "General"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    status_changed_at = models.DateTimeField(default=timezone.now)
    overdue = models.BooleanField(default=False)
    overdue_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requests")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "service_requests"
        default_permissions = ()
        permissions = [
            ("read_requests", "Can read service requests"),
            ("create_requests", "Can create service requests"),
            ("update_requests", "Can edit service requests"),
            ("delete_requests", "Can delete service requests"),
            ("update_request_status", "Can change a request's status"),
            ("read_dashboard", "Can read the dashboard summary"),
        ]
        indexes = [
            models.Index(fields=["status"], name="sr_status_idx"),
            models.Index(fields=["priority"], name="sr_priority_idx"),
            models.Index(fields=["-created_at"], name="sr_created_at_idx"),
            models.Index(
                fields=["status_changed_at"], name="sr_overdue_candidates_idx",
                condition=Q(status__in=["OPEN", "IN_PROGRESS"], overdue=False),
            ),
            models.Index(fields=["-created_at"], name="sr_overdue_idx", condition=Q(overdue=True)),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(category__in=["IT", "MAINTENANCE", "GENERAL"]), name="sr_category_chk"),
            models.CheckConstraint(condition=Q(priority__in=["LOW", "MEDIUM", "HIGH"]), name="sr_priority_chk"),
            models.CheckConstraint(condition=Q(status__in=["OPEN", "IN_PROGRESS", "RESOLVED"]), name="sr_status_chk"),
        ]

    def __str__(self):
        return f"{self.title} [{self.status}]"


class SystemState(models.Model):

    key = models.CharField(max_length=100, primary_key=True)
    value = models.TextField()
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "system_state"

    def __str__(self):
        return self.key
