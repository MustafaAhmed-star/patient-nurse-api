from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.models import JoinRequest
from apps.accounts.serializers import (
    AdminNurseSerializer,
    AdminPatientSerializer,
    BlockUserSerializer,
    JoinRequestSerializer,
    LoginSerializer,
    NurseProfileSerializer,
    NurseRegisterSerializer,
    PatientProfileSerializer,
    PatientRegisterSerializer,
    RejectJoinRequestSerializer,
    UserReadSerializer,
)
from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from shared.permissions.base import IsAdminRole, IsAuthenticatedAndNotBlocked
from shared.responses.api import ApiResponseMixin, api_response


User = get_user_model()


class PatientRegisterView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PatientRegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        data = PatientProfileSerializer(profile, context={"request": request}).data
        return api_response(
            message=_("Patient registered successfully."),
            data=data,
            status_code=status.HTTP_201_CREATED,
        )


class NurseRegisterView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = NurseRegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        data = NurseProfileSerializer(profile, context={"request": request}).data
        return api_response(
            message=_("Nurse registered successfully. Waiting for admin approval."),
            data=data,
            status_code=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return api_response(message=_("Login successful."), data=response.data)


class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return api_response(message=_("Token refreshed successfully."), data=response.data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticatedAndNotBlocked]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return api_response(
                success=False,
                message=_("Refresh token is required."),
                data={"refresh": [_("This field is required.")]},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        token = RefreshToken(refresh_token)
        token.blacklist()
        return api_response(message=_("Logout successful."))


class ProfileView(APIView):
    permission_classes = [IsAuthenticatedAndNotBlocked]

    def get_serializer(self, user, *args, **kwargs):
        if user.role == User.Role.PATIENT:
            return PatientProfileSerializer(user.patient_profile, *args, **kwargs)
        if user.role == User.Role.NURSE:
            return NurseProfileSerializer(user.nurse_profile, *args, **kwargs)
        return UserReadSerializer(user, *args, **kwargs)

    def get(self, request):
        serializer = self.get_serializer(request.user, context={"request": request})
        return api_response(message=_("Profile retrieved successfully."), data=serializer.data)

    def patch(self, request):
        if request.user.role == User.Role.ADMIN:
            return api_response(
                success=False,
                message=_("Admin profile updates are not available here."),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        instance = (
            request.user.patient_profile
            if request.user.role == User.Role.PATIENT
            else request.user.nurse_profile
        )
        serializer_class = (
            PatientProfileSerializer
            if request.user.role == User.Role.PATIENT
            else NurseProfileSerializer
        )
        serializer = serializer_class(
            instance,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_response(message=_("Profile updated successfully."), data=serializer.data)


class AdminNurseViewSet(ApiResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AdminNurseSerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ["is_blocked", "nurse_profile__is_approved", "join_request__status"]
    search_fields = ["email", "nurse_profile__full_name", "nurse_profile__phone"]
    ordering_fields = ["date_joined", "nurse_profile__full_name"]

    def get_queryset(self):
        return (
            User.objects.filter(role=User.Role.NURSE)
            .select_related("nurse_profile", "join_request")
            .order_by("-date_joined")
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        nurse = self.get_object()
        join_request = nurse.join_request
        join_request.approve(request.user)
        create_notification(
            recipient=nurse,
            title=_("Nurse account approved"),
            message=_("Your nurse account has been approved. You can now use nurse APIs."),
            notification_type=Notification.Type.ACCOUNT,
            related_join_request=join_request,
        )
        return api_response(
            message=_("Nurse approved successfully."),
            data=self.get_serializer(nurse).data,
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        serializer = RejectJoinRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nurse = self.get_object()
        join_request = nurse.join_request
        reason = serializer.validated_data.get("reason", "")
        join_request.reject(request.user, reason)
        create_notification(
            recipient=nurse,
            title=_("Nurse account rejected"),
            message=reason or _("Your nurse account was rejected by admin."),
            notification_type=Notification.Type.ACCOUNT,
            related_join_request=join_request,
        )
        return api_response(
            message=_("Nurse rejected successfully."),
            data=self.get_serializer(nurse).data,
        )

    @action(detail=True, methods=["post"])
    def block(self, request, pk=None):
        serializer = BlockUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nurse = self.get_object()
        nurse.is_blocked = serializer.validated_data["is_blocked"]
        nurse.save(update_fields=["is_blocked"])
        return api_response(message=_("Nurse block status updated."), data=self.get_serializer(nurse).data)


class AdminPatientViewSet(ApiResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AdminPatientSerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ["is_blocked"]
    search_fields = ["email", "patient_profile__full_name", "patient_profile__phone"]
    ordering_fields = ["date_joined", "patient_profile__full_name"]

    def get_queryset(self):
        return (
            User.objects.filter(role=User.Role.PATIENT)
            .select_related("patient_profile")
            .order_by("-date_joined")
        )

    @action(detail=True, methods=["post"])
    def block(self, request, pk=None):
        serializer = BlockUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient = self.get_object()
        patient.is_blocked = serializer.validated_data["is_blocked"]
        patient.save(update_fields=["is_blocked"])
        return api_response(message=_("Patient block status updated."), data=self.get_serializer(patient).data)


class JoinRequestViewSet(ApiResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = JoinRequestSerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ["status"]
    search_fields = ["nurse__email", "nurse__nurse_profile__full_name"]
    ordering_fields = ["created_at", "reviewed_at"]

    def get_queryset(self):
        return (
            JoinRequest.objects.select_related(
                "nurse",
                "nurse__nurse_profile",
                "reviewed_by",
            )
            .all()
            .order_by("-created_at")
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        join_request = self.get_object()
        join_request.approve(request.user)
        create_notification(
            recipient=join_request.nurse,
            title=_("Nurse account approved"),
            message=_("Your nurse account has been approved. You can now use nurse APIs."),
            notification_type=Notification.Type.ACCOUNT,
            related_join_request=join_request,
        )
        return api_response(
            message=_("Join request approved successfully."),
            data=self.get_serializer(join_request).data,
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        serializer = RejectJoinRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        join_request = self.get_object()
        reason = serializer.validated_data.get("reason", "")
        join_request.reject(request.user, reason)
        create_notification(
            recipient=join_request.nurse,
            title=_("Nurse account rejected"),
            message=reason or _("Your nurse account was rejected by admin."),
            notification_type=Notification.Type.ACCOUNT,
            related_join_request=join_request,
        )
        return api_response(
            message=_("Join request rejected successfully."),
            data=self.get_serializer(join_request).data,
        )
