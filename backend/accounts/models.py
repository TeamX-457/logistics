import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        DRIVER = "driver", "Driver"
        ADMIN = "admin", "Admin"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    phone_number = models.CharField(max_length=20, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"


class CustomerProfile(models.Model):
    class AccountType(models.TextChoices):
        ENTERPRISE = "enterprise", "Enterprise"
        INDIVIDUAL = "individual", "Individual"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile")
    company_name = models.CharField(max_length=255, blank=True)
    account_type = models.CharField(max_length=20, choices=AccountType.choices, default=AccountType.ENTERPRISE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name or self.user.email


class Address(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=100, blank=True)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.label or 'Address'} - {self.line1}"


class DriverProfile(models.Model):
    class VehicleType(models.TextChoices):
        BIKE = "bike", "Bike"
        MOTORCYCLE = "motorcycle", "Motorcycle"
        VAN = "van", "Van"
        CARGO_VAN = "cargo_van", "Cargo Van"
        TRUCK = "truck", "Truck"
        HEAVY_TRUCK = "heavy_truck", "Heavy Truck"

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class EntityType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        GROUP = "group", "Group"
        ENTERPRISE = "enterprise", "Enterprise"

    class Tier(models.TextChoices):
        STANDARD = "standard", "Standard"
        REPEAT = "repeat", "Repeat Driver"
        ELITE = "elite", "Elite"
        CARRIER = "carrier", "Carrier"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="driver_profile")
    vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices)
    license_number = models.CharField(max_length=50)
    nin_number = models.CharField(max_length=11, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    entity_type = models.CharField(max_length=20, choices=EntityType.choices, default=EntityType.INDIVIDUAL)
    company_name = models.CharField(max_length=255, blank=True)
    verification_status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING
    )
    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.STANDARD)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    total_trips = models.PositiveIntegerField(default=0)
    is_online = models.BooleanField(default=False)
    current_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_drivers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.vehicle_type}"


class DriverDocument(models.Model):
    class DocType(models.TextChoices):
        LICENSE_FRONT = "license_front", "License (Front)"
        LICENSE_BACK = "license_back", "License (Back)"
        NIN_CARD = "nin_card", "National ID"
        TAX_ID = "tax_id", "Tax / Business ID (CAC)"
        OTHER = "other", "Other"

    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    file = models.FileField(upload_to="driver_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver.user.email} - {self.doc_type}"


def generate_reference(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
