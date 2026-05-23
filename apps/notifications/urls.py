from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.notifications.views import AdminNotificationViewSet, NotificationViewSet


router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notifications")
router.register("admin/notifications", AdminNotificationViewSet, basename="admin-notifications")

urlpatterns = [
    path("", include(router.urls)),
]
