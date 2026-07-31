from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "client", "Client"
        DRIVER = "driver", "Driver"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=10, choices=Role.choices)
    phone_number = models.CharField(max_length=20, blank=True)
    is_available = models.BooleanField(
        default=False,
        help_text="Driver-only: whether this driver is currently on duty and eligible to see job requests.",
    )

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"
