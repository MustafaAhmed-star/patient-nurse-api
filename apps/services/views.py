from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets

from apps.services.models import Area, Service
from apps.services.serializers import AreaSerializer, ServiceSerializer
from shared.permissions.base import IsAdminRole, IsAuthenticatedAndNotBlocked
from shared.responses.api import ApiResponseMixin, api_response


class ServiceViewSet(ApiResponseMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticatedAndNotBlocked]
    filterset_fields = ["is_active"]
    search_fields = ["name_en", "name_ar", "description_en", "description_ar"]
    ordering_fields = ["name_en", "name_ar", "price", "created_at"]

    def get_queryset(self):
        return Service.objects.filter(is_active=True, is_deleted=False)


class AreaViewSet(ApiResponseMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AreaSerializer
    permission_classes = [IsAuthenticatedAndNotBlocked]
    filterset_fields = ["is_active"]
    search_fields = ["name_en", "name_ar"]
    ordering_fields = ["name_en", "name_ar", "transportation_fee", "created_at"]

    def get_queryset(self):
        return Area.objects.filter(is_active=True, is_deleted=False)


class AdminServiceViewSet(ApiResponseMixin, viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ["is_active", "is_deleted"]
    search_fields = ["name_en", "name_ar", "description_en", "description_ar"]
    ordering_fields = ["name_en", "name_ar", "price", "created_at"]

    def get_queryset(self):
        return Service.objects.all()

    def destroy(self, request, *args, **kwargs):
        service = self.get_object()
        service.soft_delete()
        return api_response(message=_("Service deleted successfully."))


class AdminAreaViewSet(ApiResponseMixin, viewsets.ModelViewSet):
    serializer_class = AreaSerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ["is_active", "is_deleted"]
    search_fields = ["name_en", "name_ar"]
    ordering_fields = ["name_en", "name_ar", "transportation_fee", "created_at"]

    def get_queryset(self):
        return Area.objects.all()

    def destroy(self, request, *args, **kwargs):
        area = self.get_object()
        area.soft_delete()
        return api_response(message=_("Area deleted successfully."))
