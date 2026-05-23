from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import UUIDTimeStampedModel


class Order(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        PENDING = "PENDING", _("Pending")
        IN_PROGRESS = "IN_PROGRESS", _("In progress")
        COMPLETED = "COMPLETED", _("Completed")
        CANCELLED = "CANCELLED", _("Cancelled")

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="patient_orders",
        limit_choices_to={"role": "PATIENT"},
    )
    nurse = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="nurse_orders",
        limit_choices_to={"role": "NURSE"},
    )
    area = models.ForeignKey(
        "services.Area",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    area_name_en = models.CharField(max_length=255)
    area_name_ar = models.CharField(max_length=255)
    address = models.TextField()
    transportation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    services_subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    cancellation_reason = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["nurse", "status"]),
        ]

    def __str__(self):
        return f"Order {self.id} - {self.status}"


class OrderItem(UUIDTimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    service_name_en = models.CharField(max_length=255)
    service_name_ar = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.service_name_en} x {self.quantity}"


class Rating(UUIDTimeStampedModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="rating")
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ratings_given",
        limit_choices_to={"role": "PATIENT"},
    )
    nurse = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ratings_received",
        limit_choices_to={"role": "NURSE"},
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.score}/5 for {self.nurse.email}"
