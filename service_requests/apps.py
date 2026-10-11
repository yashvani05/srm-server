from django.apps import AppConfig
from django.db.models.signals import post_migrate


def sync_role_groups(sender, **kwargs):
    if sender.label != "service_requests":
        return
    from django.contrib.auth.models import Group, Permission

    from accounts.roles import API_PERMISSIONS, ROLE_PERMISSIONS

    for role, api_names in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=role)
        codenames = [API_PERMISSIONS[name].split(".", 1)[1] for name in api_names]
        group.permissions.set(Permission.objects.filter(content_type__app_label="service_requests", codename__in=codenames))


class ServiceRequestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "service_requests"

    def ready(self):
        post_migrate.connect(sync_role_groups, sender=self)
