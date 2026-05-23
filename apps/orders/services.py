from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.notifications.models import Notification
from apps.notifications.services import create_notification, notify_admins, notify_order_status_changed
from apps.orders.models import Order, OrderItem
from apps.services.models import Area, Service


@transaction.atomic
def create_order(*, patient, area_id, address, services_data):
    area = Area.objects.select_for_update().get(
        id=area_id,
        is_active=True,
        is_deleted=False,
    )

    if not services_data:
        raise ValidationError({"services": _("At least one service is required.")})

    order = Order.objects.create(
        patient=patient,
        area=area,
        area_name_en=area.name_en,
        area_name_ar=area.name_ar,
        address=address,
        transportation_fee=area.transportation_fee,
    )

    subtotal = Decimal("0.00")
    for item in services_data:
        service = Service.objects.select_for_update().get(
            id=item["service_id"],
            is_active=True,
            is_deleted=False,
        )
        quantity = item.get("quantity", 1)
        total_price = service.price * quantity
        subtotal += total_price
        OrderItem.objects.create(
            order=order,
            service=service,
            service_name_en=service.name_en,
            service_name_ar=service.name_ar,
            unit_price=service.price,
            quantity=quantity,
            total_price=total_price,
        )

    order.services_subtotal = subtotal
    order.final_price = subtotal + order.transportation_fee
    order.save(update_fields=["services_subtotal", "final_price", "updated_at"])

    notify_admins(
        title=_("New order created"),
        message=_("A patient created a new order: %(order_id)s.") % {"order_id": order.id},
        notification_type=Notification.Type.ORDER,
        related_order=order,
    )
    return order


@transaction.atomic
def accept_order(*, order_id, nurse):
    order = Order.objects.select_for_update().get(id=order_id)
    if order.status != Order.Status.ACTIVE:
        raise ValidationError({"order": _("Only active orders can be accepted.")})

    has_in_progress_order = (
        Order.objects.select_for_update()
        .filter(nurse=nurse, status=Order.Status.IN_PROGRESS)
        .exists()
    )
    if has_in_progress_order:
        raise ValidationError(
            {"order": _("Nurse cannot accept more than one active order at a time.")}
        )

    order.nurse = nurse
    order.status = Order.Status.IN_PROGRESS
    order.save(update_fields=["nurse", "status", "updated_at"])

    create_notification(
        recipient=order.patient,
        title=_("Order accepted"),
        message=_("Your order %(order_id)s was accepted by a nurse.")
        % {"order_id": order.id},
        notification_type=Notification.Type.ORDER,
        related_order=order,
    )
    notify_admins(
        title=_("Order accepted"),
        message=_("Order %(order_id)s was accepted by %(nurse)s.")
        % {"order_id": order.id, "nurse": nurse.email},
        notification_type=Notification.Type.ORDER,
        related_order=order,
    )
    return order


@transaction.atomic
def complete_order(*, order_id, nurse):
    order = Order.objects.select_for_update().get(id=order_id)
    if order.nurse_id != nurse.id:
        raise PermissionDenied(_("This order is not assigned to you."))
    if order.status != Order.Status.IN_PROGRESS:
        raise ValidationError({"order": _("Only in-progress orders can be completed.")})

    order.status = Order.Status.COMPLETED
    order.completed_at = timezone.now()
    order.save(update_fields=["status", "completed_at", "updated_at"])

    notify_order_status_changed(order)
    return order


@transaction.atomic
def nurse_cancel_order(*, order_id, nurse, reason=""):
    order = Order.objects.select_for_update().get(id=order_id)
    if order.nurse_id != nurse.id:
        raise PermissionDenied(_("This order is not assigned to you."))
    if order.status != Order.Status.IN_PROGRESS:
        raise ValidationError({"order": _("Only in-progress orders can be cancelled by a nurse.")})

    order.status = Order.Status.ACTIVE
    order.nurse = None
    order.cancellation_reason = reason
    order.cancelled_at = timezone.now()
    order.save(
        update_fields=[
            "status",
            "nurse",
            "cancellation_reason",
            "cancelled_at",
            "updated_at",
        ]
    )

    create_notification(
        recipient=order.patient,
        title=_("Order returned to active"),
        message=_("Your order %(order_id)s is available for nurses again.")
        % {"order_id": order.id},
        notification_type=Notification.Type.ORDER,
        related_order=order,
    )
    notify_admins(
        title=_("Nurse cancelled accepted order"),
        message=_("Order %(order_id)s was returned to active.") % {"order_id": order.id},
        notification_type=Notification.Type.ORDER,
        related_order=order,
    )
    return order


@transaction.atomic
def admin_change_order_status(*, order_id, status, admin_user, nurse=None, reason=""):
    order = Order.objects.select_for_update().get(id=order_id)

    if status == Order.Status.ACTIVE:
        order.nurse = None
        order.completed_at = None
    elif status == Order.Status.IN_PROGRESS and nurse is not None:
        order.nurse = nurse
    elif status == Order.Status.CANCELLED:
        order.cancelled_at = timezone.now()
        order.cancellation_reason = reason
    elif status == Order.Status.COMPLETED:
        order.completed_at = timezone.now()
    elif status == Order.Status.PENDING:
        order.completed_at = None

    order.status = status
    order.save(
        update_fields=[
            "status",
            "nurse",
            "completed_at",
            "cancelled_at",
            "cancellation_reason",
            "updated_at",
        ]
    )
    notify_order_status_changed(order)
    return order
