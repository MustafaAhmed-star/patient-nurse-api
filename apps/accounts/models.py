import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from shared.validators.common import (
    validate_document_file,
    validate_egyptian_phone,
    validate_image_file,
    validate_letters_only,
)


def nurse_profile_image_path(instance, filename):
    return f"nurses/{instance.user_id}/profile/{filename}"


def nurse_document_path(instance, filename):
    return f"nurses/{instance.user_id}/documents/{filename}"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
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

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", _("Admin")
        NURSE = "NURSE", _("Nurse")
        PATIENT = "PATIENT", _("Patient")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    is_blocked = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email


class NurseProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = "MALE", _("Male")
        FEMALE = "FEMALE", _("Female")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="nurse_profile",
    )
    full_name = models.CharField(max_length=255, validators=[validate_letters_only])
    phone = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_egyptian_phone],
    )
    address = models.TextField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    wallet_number = models.CharField(max_length=30, blank=True)
    profile_image = models.ImageField(
        upload_to=nurse_profile_image_path,
        validators=[validate_image_file],
    )
    graduation_certificate = models.FileField(
        upload_to=nurse_document_path,
        validators=[validate_document_file],
    )
    syndicate_card = models.FileField(
        upload_to=nurse_document_path,
        validators=[validate_document_file],
    )
    interview_date = models.DateField()
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def approve(self):
        self.is_approved = True
        self.approved_at = timezone.now()
        self.rejected_at = None
        self.rejection_reason = ""
        self.save(
            update_fields=[
                "is_approved",
                "approved_at",
                "rejected_at",
                "rejection_reason",
                "updated_at",
            ]
        )

    def reject(self, reason=""):
        self.is_approved = False
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.save(
            update_fields=[
                "is_approved",
                "rejected_at",
                "rejection_reason",
                "updated_at",
            ]
        )

    def __str__(self):
        return self.full_name


class PatientProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
    )
    full_name = models.CharField(max_length=255, validators=[validate_letters_only])
    phone = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_egyptian_phone],
    )
    address = models.TextField()
    accepted_terms = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.full_name


class JoinRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        APPROVED = "APPROVED", _("Approved")
        REJECTED = "REJECTED", _("Rejected")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nurse = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="join_request",
        limit_choices_to={"role": User.Role.NURSE},
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_join_requests",
        limit_choices_to={"role": User.Role.ADMIN},
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def approve(self, admin_user):
        self.status = self.Status.APPROVED
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])
        self.nurse.nurse_profile.approve()

    def reject(self, admin_user, reason=""):
        self.status = self.Status.REJECTED
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.admin_notes = reason
        self.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "admin_notes",
                "updated_at",
            ]
        )
        self.nurse.nurse_profile.reject(reason)

    def __str__(self):
        return f"{self.nurse.email} - {self.status}"
