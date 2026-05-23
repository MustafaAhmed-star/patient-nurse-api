from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import JoinRequest, NurseProfile, PatientProfile
from apps.notifications.models import Notification
from apps.notifications.services import create_notification, notify_admins
from shared.validators.common import (
    validate_document_file,
    validate_egyptian_phone,
    validate_image_file,
    validate_letters_only,
    validate_strong_password,
)


User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "is_active",
            "is_blocked",
            "full_name",
            "date_joined",
        ]
        read_only_fields = fields

    def get_full_name(self, user):
        if user.role == User.Role.NURSE and hasattr(user, "nurse_profile"):
            return user.nurse_profile.full_name
        if user.role == User.Role.PATIENT and hasattr(user, "patient_profile"):
            return user.patient_profile.full_name
        return user.email


class PatientProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = PatientProfile
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "address",
            "accepted_terms",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "accepted_terms", "created_at", "updated_at"]


class NurseProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = NurseProfile
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "address",
            "gender",
            "wallet_number",
            "profile_image",
            "graduation_certificate",
            "syndicate_card",
            "interview_date",
            "is_approved",
            "approved_at",
            "rejected_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "is_approved",
            "approved_at",
            "rejected_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]


class PatientRegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    address = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    accepted_terms = serializers.BooleanField()

    def validate_full_name(self, value):
        validate_letters_only(value)
        return value

    def validate_phone(self, value):
        validate_egyptian_phone(value)
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("This email is already registered."))
        return value.lower()

    def validate_password(self, value):
        validate_strong_password(value)
        return value

    def validate_accepted_terms(self, value):
        if value is not True:
            raise serializers.ValidationError(_("You must accept the terms and conditions."))
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=password,
            role=User.Role.PATIENT,
        )
        profile = PatientProfile.objects.create(
            user=user,
            full_name=validated_data["full_name"],
            phone=validated_data["phone"],
            address=validated_data["address"],
            accepted_terms=True,
        )
        return profile


class NurseRegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    address = serializers.CharField()
    gender = serializers.ChoiceField(choices=NurseProfile.Gender.choices)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    profile_image = serializers.ImageField(validators=[validate_image_file])
    graduation_certificate = serializers.FileField(validators=[validate_document_file])
    syndicate_card = serializers.FileField(validators=[validate_document_file])
    interview_date = serializers.DateField()
    wallet_number = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def validate_full_name(self, value):
        validate_letters_only(value)
        return value

    def validate_phone(self, value):
        validate_egyptian_phone(value)
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("This email is already registered."))
        return value.lower()

    def validate_password(self, value):
        validate_strong_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=password,
            role=User.Role.NURSE,
        )
        profile = NurseProfile.objects.create(
            user=user,
            full_name=validated_data["full_name"],
            phone=validated_data["phone"],
            address=validated_data["address"],
            gender=validated_data["gender"],
            wallet_number=validated_data.get("wallet_number", ""),
            profile_image=validated_data["profile_image"],
            graduation_certificate=validated_data["graduation_certificate"],
            syndicate_card=validated_data["syndicate_card"],
            interview_date=validated_data["interview_date"],
        )
        join_request = JoinRequest.objects.create(nurse=user)

        notify_admins(
            title=_("New nurse join request"),
            message=_("%(name)s registered as a nurse and is waiting for approval.")
            % {"name": profile.full_name},
            notification_type=Notification.Type.JOIN_REQUEST,
            related_join_request=join_request,
        )
        return profile


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        if user.is_blocked:
            raise serializers.ValidationError(_("This account is blocked."))
        data["user"] = UserReadSerializer(user).data
        return data


class JoinRequestSerializer(serializers.ModelSerializer):
    nurse = UserReadSerializer(read_only=True)
    nurse_profile = serializers.SerializerMethodField()
    reviewed_by = UserReadSerializer(read_only=True)

    class Meta:
        model = JoinRequest
        fields = [
            "id",
            "nurse",
            "nurse_profile",
            "status",
            "reviewed_by",
            "reviewed_at",
            "admin_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_nurse_profile(self, obj):
        if hasattr(obj.nurse, "nurse_profile"):
            return NurseProfileSerializer(obj.nurse.nurse_profile, context=self.context).data
        return None


class AdminNurseSerializer(serializers.ModelSerializer):
    profile = NurseProfileSerializer(source="nurse_profile", read_only=True)
    join_request_status = serializers.CharField(source="join_request.status", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "is_active",
            "is_blocked",
            "profile",
            "join_request_status",
            "date_joined",
        ]
        read_only_fields = fields


class AdminPatientSerializer(serializers.ModelSerializer):
    profile = PatientProfileSerializer(source="patient_profile", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "is_active",
            "is_blocked",
            "profile",
            "date_joined",
        ]
        read_only_fields = fields


class BlockUserSerializer(serializers.Serializer):
    is_blocked = serializers.BooleanField()


class RejectJoinRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)
