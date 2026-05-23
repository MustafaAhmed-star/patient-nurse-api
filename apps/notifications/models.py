from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import UUIDTimeStampedModel


class Notification(UUIDTimeStampedModel):
    class Type(models.TextChoices):
        ACCOUNT = "ACCOUNT", _("Account")
        ORDER = "ORDER", _("Order")
        JOIN_REQUEST = "JOIN_REQUEST", _("Join request")

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=Type.choices)
    related_order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    related_join_request = models.ForeignKey(
        "accounts.JoinRequest",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    email_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["notification_type", "created_at"]),
        ]

    def __str__(self):
        return self.title
