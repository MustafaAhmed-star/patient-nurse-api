from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.notifications.models import Notification


def create_notification(
    *,
    recipient,
    title,
    message,
    notification_type,
    related_order=None,
    related_join_request=None,
    send_email=True,
):
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        related_order=related_order,
        related_join_request=related_join_request,
    )

    if send_email and recipient.email:
        sent = send_mail(
            subject=title,
            message=message,
            from_email=None,
            recipient_list=[recipient.email],
            fail_silently=True,
        )
        if sent:
            notification.email_sent = True
            notification.save(update_fields=["email_sent", "updated_at"])

    return notification


def notify_admins(*, title, message, notification_type, related_order=None, related_join_request=None):
    User = get_user_model()
    admins = User.objects.filter(role=User.Role.ADMIN, is_active=True, is_blocked=False)
    notifications = []
    for admin in admins:
        notifications.append(
            create_notification(
                recipient=admin,
                title=title,
                message=message,
                notification_type=notification_type,
                related_order=related_order,
                related_join_request=related_join_request,
            )
        )
    return notifications


def mark_notification_read(notification):
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save(update_fields=["is_read", "read_at", "updated_at"])
    return notification


def notify_order_status_changed(order):
    title = _("Order status updated")
    message = _("Order %(order_id)s is now %(status)s.") % {
        "order_id": order.id,
        "status": order.status,
    }
    create_notification(
        recipient=order.patient,
        title=title,
        message=message,
        notification_type=Notification.Type.ORDER,
        related_order=order,
    )
    if order.nurse:
        create_notification(
            recipient=order.nurse,
            title=title,
            message=message,
            notification_type=Notification.Type.ORDER,
            related_order=order,
        )
    notify_admins(
        title=title,
        message=message,
        notification_type=Notification.Type.ORDER,
        related_order=order,
    )
