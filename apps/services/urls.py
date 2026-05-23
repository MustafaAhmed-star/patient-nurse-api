from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.services.views import AdminAreaViewSet, AdminServiceViewSet, AreaViewSet, ServiceViewSet


router = DefaultRouter()
router.register("services", ServiceViewSet, basename="services")
router.register("areas", AreaViewSet, basename="areas")
router.register("admin/services", AdminServiceViewSet, basename="admin-services")
router.register("admin/areas", AdminAreaViewSet, basename="admin-areas")

urlpatterns = [
    path("", include(router.urls)),
]
