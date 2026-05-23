from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "notification_type",
            "related_order",
            "related_join_request",
            "is_read",
            "read_at",
            "email_sent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
