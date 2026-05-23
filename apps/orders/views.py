from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action

from apps.notifications.models import Notification
from apps.notifications.services import create_notification, notify_order_status_changed
from apps.orders.models import Order, Rating
from apps.orders.serializers import (
    AdminOrderStatusSerializer,
    AdminOrderUpdateSerializer,
    NurseEarningsSerializer,
    OrderCreateSerializer,
    OrderReadSerializer,
    RatingSerializer,
)
from apps.orders.services import (
    accept_order,
    admin_change_order_status,
    complete_order,
    nurse_cancel_order,
)
from shared.permissions.base import IsAdminRole, IsApprovedNurseRole, IsPatientRole
from shared.responses.api import ApiResponseMixin, api_response


class PatientOrderViewSet(ApiResponseMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsPatientRole]
    filterset_fields = ["status", "area"]
    search_fields = ["address", "area_name_en", "area_name_ar"]
    ordering_fields = ["created_at", "final_price", "status"]

    def get_queryset(self):
        return (
            Order.objects.filter(patient=self.request.user)
            .select_related("patient", "nurse", "area")
            .prefetch_related("items")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        data = OrderReadSerializer(order, context={"request": request}).data
        return api_response(
            message=_("Order created successfully."),
            data=data,
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def rate(self, request, pk=None):
        order = self.get_object()
        serializer = RatingSerializer(
            data=request.data,
            context={"request": request, "order": order},
        )
        serializer.is_valid(raise_exception=True)
        rating = serializer.save()
        create_notification(
            recipient=order.nurse,
            title=_("New rating received"),
            message=_("You received a new rating for order %(order_id)s.")
            % {"order_id": order.id},
            notification_type=Notification.Type.ORDER,
            related_order=order,
        )
        return api_response(
            message=_("Rating submitted successfully."),
            data=RatingSerializer(rating).data,
            status_code=status.HTTP_201_CREATED,
        )


class NurseOrderViewSet(ApiResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderReadSerializer
    permission_classes = [IsApprovedNurseRole]
    filterset_fields = ["status", "area"]
    search_fields = ["address", "area_name_en", "area_name_ar"]
    ordering_fields = ["created_at", "final_price", "status"]

    def get_queryset(self):
        return (
            Order.objects.filter(Q(status=Order.Status.ACTIVE) | Q(nurse=self.request.user))
            .select_related("patient", "nurse", "area")
            .prefetch_related("items")
        )

    @action(detail=False, methods=["get"])
    def active(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(status=Order.Status.ACTIVE)
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return api_response(message=_("Active orders retrieved successfully."), data=serializer.data)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        order = accept_order(order_id=pk, nurse=request.user)
        return api_response(
            message=_("Order accepted successfully."),
            data=self.get_serializer(order).data,
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        order = complete_order(order_id=pk, nurse=request.user)
        return api_response(
            message=_("Order completed successfully."),
            data=self.get_serializer(order).data,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        reason = request.data.get("reason", "")
        order = nurse_cancel_order(order_id=pk, nurse=request.user, reason=reason)
        return api_response(
            message=_("Order cancelled and returned to active successfully."),
            data=self.get_serializer(order).data,
        )

    @action(detail=False, methods=["get"])
    def earnings(self, request):
        data = NurseEarningsSerializer.build(request.user)
        serializer = NurseEarningsSerializer(data)
        return api_response(message=_("Earnings retrieved successfully."), data=serializer.data)

    @action(detail=False, methods=["get"])
    def ratings(self, request):
        queryset = Rating.objects.filter(nurse=request.user).select_related("order", "patient", "nurse")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = RatingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return api_response(
            message=_("Ratings retrieved successfully."),
            data=RatingSerializer(queryset, many=True).data,
        )


class AdminOrderViewSet(ApiResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAdminRole]
    filterset_fields = ["status", "area", "patient", "nurse"]
    search_fields = ["address", "area_name_en", "area_name_ar", "patient__email", "nurse__email"]
    ordering_fields = ["created_at", "final_price", "status"]

    def get_queryset(self):
        return (
            Order.objects.select_related("patient", "nurse", "area")
            .prefetch_related("items")
            .all()
        )

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return AdminOrderUpdateSerializer
        return OrderReadSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        notify_order_status_changed(instance)
        return api_response(
            message=_("Order updated successfully."),
            data=OrderReadSerializer(instance, context={"request": request}).data,
        )

    @action(detail=True, methods=["post"], url_path="change-status")
    def change_status(self, request, pk=None):
        serializer = AdminOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = admin_change_order_status(
            order_id=pk,
            status=serializer.validated_data["status"],
            nurse=serializer.validated_data.get("nurse"),
            admin_user=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )
        return api_response(
            message=_("Order status updated successfully."),
            data=OrderReadSerializer(order, context={"request": request}).data,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = admin_change_order_status(
            order_id=pk,
            status=Order.Status.CANCELLED,
            admin_user=request.user,
            reason=request.data.get("reason", ""),
        )
        return api_response(
            message=_("Order cancelled successfully."),
            data=OrderReadSerializer(order, context={"request": request}).data,
        )
