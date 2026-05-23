from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.orders.views import AdminOrderViewSet, NurseOrderViewSet, PatientOrderViewSet


router = DefaultRouter()
router.register("patient/orders", PatientOrderViewSet, basename="patient-orders")
router.register("nurse/orders", NurseOrderViewSet, basename="nurse-orders")
router.register("admin/orders", AdminOrderViewSet, basename="admin-orders")

urlpatterns = [
    path("", include(router.urls)),
]
