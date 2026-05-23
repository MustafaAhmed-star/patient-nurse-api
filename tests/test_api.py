from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import NurseProfile, PatientProfile
from apps.notifications.models import Notification
from apps.orders.models import Order
from apps.services.models import Area, Service


User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class RegistrationApiTests(APITestCase):
    def test_patient_must_accept_terms(self):
        response = self.client.post(
            "/api/v1/auth/register/patient/",
            {
                "full_name": "Ahmed Ali",
                "phone": "01012345678",
                "email": "patient@example.com",
                "address": "Cairo",
                "password": "Strong!123",
                "accepted_terms": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_email_cannot_be_reused_across_roles(self):
        User.objects.create_user(
            email="same@example.com",
            password="Strong!123",
            role=User.Role.NURSE,
        )

        response = self.client.post(
            "/api/v1/auth/register/patient/",
            {
                "full_name": "Ahmed Ali",
                "phone": "01012345678",
                "email": "same@example.com",
                "address": "Cairo",
                "password": "Strong!123",
                "accepted_terms": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class OrderApiTests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            email="patient@example.com",
            password="Strong!123",
            role=User.Role.PATIENT,
        )
        PatientProfile.objects.create(
            user=self.patient,
            full_name="Ahmed Ali",
            phone="01012345678",
            address="Cairo",
            accepted_terms=True,
        )
        self.nurse = User.objects.create_user(
            email="nurse@example.com",
            password="Strong!123",
            role=User.Role.NURSE,
        )
        NurseProfile.objects.create(
            user=self.nurse,
            full_name="Sara Ali",
            phone="01112345678",
            address="Cairo",
            gender=NurseProfile.Gender.FEMALE,
            profile_image="nurses/test/profile.jpg",
            graduation_certificate="nurses/test/certificate.pdf",
            syndicate_card="nurses/test/card.pdf",
            interview_date="2026-06-01",
            is_approved=True,
        )
        self.area = Area.objects.create(
            name_en="Inside City",
            name_ar="داخل المدينة",
            transportation_fee=Decimal("25.00"),
        )
        self.service = Service.objects.create(
            name_en="IV Fluids",
            name_ar="محاليل",
            price=Decimal("100.00"),
        )

    def create_order(self):
        self.client.force_authenticate(self.patient)
        response = self.client.post(
            "/api/v1/patient/orders/",
            {
                "area_id": str(self.area.id),
                "address": "Home address",
                "services": [{"service_id": str(self.service.id), "quantity": 2}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Order.objects.get(id=response.data["data"]["id"])

    def test_patient_order_snapshots_prices(self):
        order = self.create_order()

        self.assertEqual(order.services_subtotal, Decimal("200.00"))
        self.assertEqual(order.transportation_fee, Decimal("25.00"))
        self.assertEqual(order.final_price, Decimal("225.00"))

        self.service.price = Decimal("500.00")
        self.service.save()
        order.refresh_from_db()

        self.assertEqual(order.final_price, Decimal("225.00"))

    def test_nurse_accept_sets_in_progress_and_blocks_second_active_order(self):
        first_order = self.create_order()
        second_order = self.create_order()

        self.client.force_authenticate(self.nurse)
        first_response = self.client.post(f"/api/v1/nurse/orders/{first_order.id}/accept/")
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        first_order.refresh_from_db()
        self.assertEqual(first_order.status, Order.Status.IN_PROGRESS)

        second_response = self.client.post(f"/api/v1/nurse/orders/{second_order.id}/accept/")
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        second_order.refresh_from_db()
        self.assertEqual(second_order.status, Order.Status.ACTIVE)


class NotificationApiTests(APITestCase):
    def test_user_can_mark_own_notification_as_read(self):
        user = User.objects.create_user(
            email="patient@example.com",
            password="Strong!123",
            role=User.Role.PATIENT,
        )
        notification = Notification.objects.create(
            recipient=user,
            title="Hello",
            message="Message",
            notification_type=Notification.Type.ACCOUNT,
        )

        self.client.force_authenticate(user)
        response = self.client.post(f"/api/v1/notifications/{notification.id}/mark-read/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
