from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Address, CustomerProfile, DriverDocument, DriverProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "role", "is_staff", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone_number", "avatar", "role")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "password1", "password2", "role")}),
    )


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "company_name", "account_type"]
    search_fields = ["user__email", "company_name"]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["customer", "label", "city", "is_default"]


class DriverDocumentInline(admin.TabularInline):
    model = DriverDocument
    extra = 0


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "vehicle_type", "entity_type", "verification_status", "rating", "is_online"]
    list_filter = ["verification_status", "vehicle_type", "entity_type"]
    search_fields = ["user__email", "license_number", "nin_number"]
    inlines = [DriverDocumentInline]
