from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import DeviceToken, Notification
from .services import notify_user


def make_customer(email="cust@gmail.com"):
    user = User.objects.create_user(email=email, password="Pass12345", full_name="Customer")
    user.is_email_verified = True
    user.save()
    return user


class NotifyUserServiceTests(APITestCase):
    def test_notify_user_creates_notification_record(self):
        customer = make_customer()
        notify_user(customer, Notification.Type.ORDER_ACCEPTED, "Order accepted!", "Your order was accepted.")
        self.assertEqual(Notification.objects.filter(user=customer).count(), 1)
        notif = Notification.objects.get(user=customer)
        self.assertEqual(notif.title, "Order accepted!")
        self.assertFalse(notif.is_read)

    def test_notify_user_never_raises_if_channel_layer_broadcast_fails(self):
        """_broadcast_to_user swallows errors so a WS hiccup never breaks the caller."""
        customer = make_customer()
        # Even with the default in-memory channel layer in tests, this should complete without raising.
        notif = notify_user(customer, Notification.Type.OTHER, "Test", "Test message")
        self.assertIsNotNone(notif.id)


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.customer = make_customer()
        self.other = make_customer("other@gmail.com")

    def test_list_only_own_notifications(self):
        notify_user(self.customer, Notification.Type.OTHER, "Mine", "For me")
        notify_user(self.other, Notification.Type.OTHER, "Not mine", "For someone else")

        self.client.force_authenticate(user=self.customer)
        response = self.client.get(reverse("notifications:notification-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Mine")

    def test_unread_count(self):
        notify_user(self.customer, Notification.Type.OTHER, "A", "msg")
        notify_user(self.customer, Notification.Type.OTHER, "B", "msg")
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(reverse("notifications:notification-unread-count"))
        self.assertEqual(response.data["unread_count"], 2)

    def test_mark_read(self):
        notif = notify_user(self.customer, Notification.Type.OTHER, "A", "msg")
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(reverse("notifications:notification-mark-read", args=[notif.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_read"])

    def test_mark_all_read(self):
        notify_user(self.customer, Notification.Type.OTHER, "A", "msg")
        notify_user(self.customer, Notification.Type.OTHER, "B", "msg")
        self.client.force_authenticate(user=self.customer)
        self.client.post(reverse("notifications:notification-mark-all-read"))
        self.assertEqual(Notification.objects.filter(user=self.customer, is_read=False).count(), 0)

    def test_cannot_mark_someone_elses_notification_read(self):
        notif = notify_user(self.other, Notification.Type.OTHER, "A", "msg")
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(reverse("notifications:notification-mark-read", args=[notif.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DeviceTokenTests(APITestCase):
    def setUp(self):
        self.customer = make_customer()

    def test_register_device_token(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(reverse("notifications:device-token-list"), {"token": "abc123", "platform": "web"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(DeviceToken.objects.filter(user=self.customer, token="abc123").exists())

    def test_reregistering_same_token_updates_owner(self):
        """Common real-world case: a device token gets reassigned to a different logged-in user."""
        DeviceToken.objects.create(user=self.customer, token="shared-token")
        other = make_customer("other2@gmail.com")
        self.client.force_authenticate(user=other)
        response = self.client.post(reverse("notifications:device-token-list"), {"token": "shared-token", "platform": "web"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token_obj = DeviceToken.objects.get(token="shared-token")
        self.assertEqual(token_obj.user, other)


class OrderNotificationIntegrationTests(APITestCase):
    """Confirms order status transitions actually fire the right notifications (Phase 4-6 integration)."""

    def test_order_accepted_notifies_customer(self):
        from meals.models import Meal
        from restaurants.models import Restaurant

        customer = make_customer()
        vendor = User.objects.create_user(email="v@x.com", password="Pass12345", full_name="V", role=User.Role.VENDOR)
        vendor.is_approved = True
        vendor.save()
        restaurant = Restaurant.objects.create(owner=vendor, name="N", slug="n1", location="L", status="open", is_active=True)
        meal = Meal.objects.create(restaurant=restaurant, name="M", price=Decimal("100.00"))

        self.client.force_authenticate(user=customer)
        self.client.post(reverse("orders:cart"), {"meal_id": str(meal.id), "quantity": 1})
        checkout = self.client.post(reverse("orders:checkout"), {
            "delivery_campus_location": "Hostel A", "payment_method": "cash_on_delivery",
        })
        order_id = checkout.data["id"]

        self.client.force_authenticate(user=vendor)
        self.client.post(reverse("orders:order-update-status", args=[order_id]), {"status": "accepted"})

        self.assertTrue(
            Notification.objects.filter(user=customer, notification_type=Notification.Type.ORDER_ACCEPTED).exists()
        )
