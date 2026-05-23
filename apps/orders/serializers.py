from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.accounts.serializers import UserReadSerializer
from apps.orders.models import Order, OrderItem, Rating
from apps.orders.services import create_order
from apps.services.models import Area, Service


User = get_user_model()


class OrderServiceInputSerializer(serializers.Serializer):
    service_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_service_id(self, value):
        if not Service.objects.filter(id=value, is_active=True, is_deleted=False).exists():
            raise serializers.ValidationError(_("Service does not exist or is inactive."))
        return value


class OrderItemReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "service",
            "service_name_en",
            "service_name_ar",
            "unit_price",
            "quantity",
            "total_price",
        ]
        read_only_fields = fields


class OrderReadSerializer(serializers.ModelSerializer):
    patient = UserReadSerializer(read_only=True)
    nurse = UserReadSerializer(read_only=True)
    items = OrderItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "patient",
            "nurse",
            "area",
            "area_name_en",
            "area_name_ar",
            "address",
            "transportation_fee",
            "services_subtotal",
            "final_price",
            "status",
            "cancellation_reason",
            "completed_at",
            "cancelled_at",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    area_id = serializers.UUIDField()
    address = serializers.CharField()
    services = OrderServiceInputSerializer(many=True)

    def validate_area_id(self, value):
        if not Area.objects.filter(id=value, is_active=True, is_deleted=False).exists():
            raise serializers.ValidationError(_("Area does not exist or is inactive."))
        return value

    def create(self, validated_data):
        return create_order(
            patient=self.context["request"].user,
            area_id=validated_data["area_id"],
            address=validated_data["address"],
            services_data=validated_data["services"],
        )


class AdminOrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["address", "cancellation_reason"]

class AdminOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
    nurse_id = serializers.UUIDField(required=False, allow_null=True)
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        status = attrs["status"]
        nurse_id = attrs.get("nurse_id")
        if status == Order.Status.IN_PROGRESS:
            if not nurse_id:
                raise serializers.ValidationError(
                    {"nurse_id": _("A nurse is required for IN_PROGRESS orders.")}
                )
            nurse = User.objects.filter(id=nurse_id, role=User.Role.NURSE).first()
            if nurse is None:
                raise serializers.ValidationError({"nurse_id": _("Nurse not found.")})
            if not hasattr(nurse, "nurse_profile") or not nurse.nurse_profile.is_approved:
                raise serializers.ValidationError(
                    {"nurse_id": _("Nurse must be approved.")}
                )
            attrs["nurse"] = nurse
        return attrs


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ["id", "order", "patient", "nurse", "score", "comment", "created_at"]
        read_only_fields = ["id", "order", "patient", "nurse", "created_at"]

    def validate(self, attrs):
        order = self.context["order"]
        request = self.context["request"]
        if order.patient_id != request.user.id:
            raise serializers.ValidationError(_("You can rate only your own orders."))
        if order.status != Order.Status.COMPLETED:
            raise serializers.ValidationError(_("Only completed orders can be rated."))
        if not order.nurse_id:
            raise serializers.ValidationError(_("This order does not have an assigned nurse."))
        if hasattr(order, "rating"):
            raise serializers.ValidationError(_("This order was already rated."))
        return attrs

    def create(self, validated_data):
        order = self.context["order"]
        return Rating.objects.create(
            order=order,
            patient=order.patient,
            nurse=order.nurse,
            **validated_data,
        )


class NurseEarningsSerializer(serializers.Serializer):
    completed_orders = serializers.IntegerField()
    total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)

    @staticmethod
    def build(nurse):
        completed = Order.objects.filter(nurse=nurse, status=Order.Status.COMPLETED)
        return {
            "completed_orders": completed.count(),
            "total_earnings": completed.aggregate(total=Sum("final_price"))["total"] or 0,
        }
