from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins, viewsets
from rest_framework.decorators import action

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.services import mark_notification_read
from shared.permissions.base import IsAdminRole, IsAuthenticatedAndNotBlocked
from shared.responses.api import ApiResponseMixin, api_response


class NotificationViewSet(ApiResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticatedAndNotBlocked]
    filterset_fields = ["is_read", "notification_type"]
    search_fields = ["title", "message"]
    ordering_fields = ["created_at", "is_read"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return api_response(message=_("Unread count retrieved successfully."), data={"count": count})

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        mark_notification_read(notification)
        return api_response(
            message=_("Notification marked as read."),
            data=self.get_serializer(notification).data,
        )

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now(),
        )
        return api_response(
            message=_("All notifications marked as read."),
            data={"updated": updated},
        )


class AdminNotificationViewSet(NotificationViewSet):
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        return Notification.objects.select_related("recipient").all()
