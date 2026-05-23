from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import SoftDeleteModel


class Service(SoftDeleteModel):
    name_en = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255)
    description_en = models.TextField(blank=True)
    description_ar = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        ordering = ["name_en"]
        indexes = [
            models.Index(fields=["is_active", "is_deleted"]),
            models.Index(fields=["name_en"]),
            models.Index(fields=["name_ar"]),
        ]

    def __str__(self):
        return f"{self.name_en} / {self.name_ar}"


class Area(SoftDeleteModel):
    name_en = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255)
    transportation_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        ordering = ["name_en"]
        indexes = [
            models.Index(fields=["is_active", "is_deleted"]),
            models.Index(fields=["name_en"]),
            models.Index(fields=["name_ar"]),
        ]

    def __str__(self):
        return f"{self.name_en} / {self.name_ar}"
