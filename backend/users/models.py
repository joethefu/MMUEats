import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from common.models import TimeStampedModel
from .managers import UserManager

phone_validator = RegexValidator(
    regex=r"^\+?[0-9]{9,15}$",
    message="Enter a valid phone number, e.g. +254712345678",
)


class User(AbstractUser):
    """
    Custom user model. Email is the primary login credential; username is kept
    (from AbstractUser) but auto-derived and not used for login.

    IMPORTANT: registration is intentionally NOT restricted to any university
    email domain — students/staff sign up with any Gmail/other supported email.
    """

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        VENDOR = "vendor", "Vendor"
        DELIVERY_PARTNER = "delivery_partner", "Delivery Partner"
        ADMIN = "admin", "Administrator"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, validators=[phone_validator], blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)

    # Email verification gate — accounts cannot log in until True.
    is_email_verified = models.BooleanField(default=False)

    # Vendors and Delivery Partners require admin approval before their role
    # functionality is usable. Customers and Admins are approved by default.
    is_approved = models.BooleanField(default=True)

    is_suspended = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "full_name"]

    objects = UserManager()

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["email"]),
        ]

    def save(self, *args, **kwargs):
        # Vendors / delivery partners start unapproved until admin review.
        if self._state.adding and self.role in (self.Role.VENDOR, self.Role.DELIVERY_PARTNER):
            self.is_approved = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class DeliveryLocation(TimeStampedModel):
    """A customer's saved delivery location (campus hostel, block, etc.)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_locations")
    label = models.CharField(max_length=100)  # e.g. "Hostel C - Room 214"
    campus_location = models.CharField(max_length=100)  # e.g. "Hostel C"
    additional_directions = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.label} ({self.user.email})"


class ApplicationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    NEEDS_INFO = "needs_info", "Needs More Information"


class VendorApplication(TimeStampedModel):
    """
    Spec §17: submitted from the public 'Become a Vendor' page — NOT part of the
    main customer Sign Up. Approval creates/activates the applicant's User account
    with role=vendor.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business_name = models.CharField(max_length=150)
    owner_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, validators=[phone_validator])
    business_location = models.CharField(max_length=255)
    food_categories = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="vendor_applications/logos/", null=True, blank=True)

    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.PENDING)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_vendor_applications"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    # Populated once approved and the vendor account is created.
    resulting_user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="vendor_application"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.business_name} ({self.status})"


class DeliveryPartnerApplication(TimeStampedModel):
    """Spec §18: submitted from the public 'Become a Delivery Partner' page."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, validators=[phone_validator])
    preferred_area = models.CharField(max_length=150)
    availability = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(upload_to="delivery_partner_applications/", null=True, blank=True)

    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.PENDING)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_delivery_applications"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    resulting_user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="delivery_partner_application"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.full_name} ({self.status})"
