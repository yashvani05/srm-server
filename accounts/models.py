import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import Group, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower

from . import roles


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, name, password=None, role=roles.EMPLOYEE, **extra):
        user = self.model(email=email.strip().lower(), name=name.strip(), is_staff=(role == roles.ADMIN), **extra)
        user.set_password(password)
        user.save(using=self._db)
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
        return user

    def create_superuser(self, email, name, password=None, **extra):
        return self.create_user(email, name, password, role=roles.ADMIN, is_superuser=True, **extra)


class User(AbstractBaseUser, PermissionsMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users"
        constraints = [models.UniqueConstraint(Lower("email"), name="users_email_lower_uq")]

    def __str__(self):
        return self.email

    @property
    def role(self) -> str:
        return roles.ADMIN if self.groups.filter(name=roles.ADMIN).exists() else roles.EMPLOYEE

    @property
    def api_permissions(self) -> list[str]:
        held = self.get_all_permissions()
        return [api for api, django_perm in roles.API_PERMISSIONS.items() if django_perm in held]
