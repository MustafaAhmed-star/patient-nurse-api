from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import (
    AdminNurseViewSet,
    AdminPatientViewSet,
    JoinRequestViewSet,
    LoginView,
    LogoutView,
    NurseRegisterView,
    PatientRegisterView,
    ProfileView,
    RefreshTokenView,
)


router = DefaultRouter()
router.register("admin/nurses", AdminNurseViewSet, basename="admin-nurses")
router.register("admin/patients", AdminPatientViewSet, basename="admin-patients")
router.register("admin/join-requests", JoinRequestViewSet, basename="admin-join-requests")

urlpatterns = [
    path("auth/register/patient/", PatientRegisterView.as_view(), name="register-patient"),
    path("auth/register/nurse/", NurseRegisterView.as_view(), name="register-nurse"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/token/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("", include(router.urls)),
]
