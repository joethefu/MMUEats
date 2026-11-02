from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from meals.models import Meal
from orders.models import Order
from restaurants.models import Restaurant
from users.models import User

from .models import Delivery, DeliveryPartnerProfile


def make_customer(email="cust@gmail.com"):
    user = User.objects.create_user(email=email, password="Pass12345", full_name="Customer")
    user.is_email_verified = True
    user.save()
    return user


def make_vendor_with_restaurant(email="vendor@x.com"):
    vendor = User.objects.create_user(email=email, password="Pass12345", full_name="Vendor", role=User.Role.VENDOR)
    vendor.is_approved = True
    vendor.is_email_verified = True
    vendor.save()
    restaurant = Restaurant.objects.create(
        owner=vendor, name="D Kitchen", slug=f"dk-{vendor.id}", location="Loc",
        status="open", is_active=True, delivery_fee=Decimal("60.00"),
    )
    return vendor, restaurant


def make_delivery_partner(email="rider@x.com"):
    partner = User.objects.create_user(
        email=email, password="Pass12345", full_name="Rider", role=User.Role.DELIVERY_PARTNER
    )
    partner.is_approved = True
    partner.is_email_verified = True
    partner.save()
    return partner


def create_ready_order(customer, vendor, restaurant, meal_price=Decimal("300.00")):
    """Builds an order and drives it to 'ready_for_pickup' via the real API, as a vendor would."""
    from rest_framework.test import APIClient

    meal = Meal.objects.create(restaurant=restaurant, name="Test Meal", price=meal_price)
    client = APIClient()
    client.force_authenticate(user=customer)
    client.post(reverse("orders:cart"), {"meal_id": str(meal.id), "quantity": 1})
    checkout = client.post(reverse("orders:checkout"), {
        "delivery_campus_location": "Hostel A", "payment_method": "cash_on_delivery",
    })
    order_id = checkout.data["id"]

    client.force_authenticate(user=vendor)
    status_url = lambda: reverse("orders:order-update-status", args=[order_id])
    client.post(status_url(), {"status": "accepted"})
    client.post(status_url(), {"status": "preparing"})
    client.post(status_url(), {"status": "ready_for_pickup"})

    return Order.objects.get(pk=order_id)


class DeliveryPoolTests(APITestCase):
    def setUp(self):
        self.customer = make_customer()
        self.vendor, self.restaurant = make_vendor_with_restaurant()
        self.partner = make_delivery_partner()

    def test_ready_for_pickup_creates_delivery_in_pool(self):
        order = create_ready_order(self.customer, self.vendor, self.restaurant)
        self.assertTrue(Delivery.objects.filter(order=order, delivery_partner__isnull=True).exists())

    def test_partner_sees_available_delivery(self):
        create_ready_order(self.customer, self.vendor, self.restaurant)
        self.client.force_authenticate(user=self.partner)
        response = self.client.get(reverse("deliveries:available"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_customer_cannot_see_available_deliveries(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(reverse("deliveries:available"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partner_can_accept_available_delivery(self):
        order = create_ready_order(self.customer, self.vendor, self.restaurant)
        delivery = Delivery.objects.get(order=order)
        self.client.force_authenticate(user=self.partner)
        response = self.client.post(reverse("deliveries:my-delivery-accept", args=[delivery.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        delivery.refresh_from_db()
        self.assertEqual(delivery.delivery_partner, self.partner)

    def test_two_partners_cannot_both_accept_same_delivery(self):
        order = create_ready_order(self.customer, self.vendor, self.restaurant)
        delivery = Delivery.objects.get(order=order)
        other_partner = make_delivery_partner("rider2@x.com")

        self.client.force_authenticate(user=self.partner)
        self.client.post(reverse("deliveries:my-delivery-accept", args=[delivery.pk]))

        self.client.force_authenticate(user=other_partner)
        response = self.client.post(reverse("deliveries:my-delivery-accept", args=[delivery.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # already taken

    def test_partner_can_reject_before_pickup_releasing_to_pool(self):
        order = create_ready_order(self.customer, self.vendor, self.restaurant)
        delivery = Delivery.objects.get(order=order)
        self.client.force_authenticate(user=self.partner)
        self.client.post(reverse("deliveries:my-delivery-accept", args=[delivery.pk]))
        response = self.client.post(reverse("deliveries:my-delivery-reject", args=[delivery.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        delivery.refresh_from_db()
        self.assertIsNone(delivery.delivery_partner)


class DeliveryLifecycleTests(APITestCase):
    def setUp(self):
        self.customer = make_customer()
        self.vendor, self.restaurant = make_vendor_with_restaurant()
        self.partner = make_delivery_partner()
        self.order = create_ready_order(self.customer, self.vendor, self.restaurant, meal_price=Decimal("300.00"))
        self.delivery = Delivery.objects.get(order=self.order)

        self.client.force_authenticate(user=self.partner)
        self.client.post(reverse("deliveries:my-delivery-accept", args=[self.delivery.pk]))

    def status_url(self):
        return reverse("orders:order-update-status", args=[self.order.pk])

    def test_assigned_partner_can_progress_order_to_delivered(self):
        for target in ["picked_up", "out_for_delivery", "delivered"]:
            response = self.client.post(self.status_url(), {"status": target})
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "delivered")

        self.delivery.refresh_from_db()
        self.assertIsNotNone(self.delivery.delivered_at)
        self.assertEqual(self.delivery.earnings, self.restaurant.delivery_fee)

    def test_vendor_cannot_perform_delivery_partner_transitions(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.post(self.status_url(), {"status": "picked_up"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "permission_denied")

    def test_unassigned_partner_cannot_see_or_update_order(self):
        other_partner = make_delivery_partner("outsider@x.com")
        self.client.force_authenticate(user=other_partner)
        response = self.client.post(self.status_url(), {"status": "picked_up"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delivery_completion_updates_partner_earnings(self):
        self.client.post(self.status_url(), {"status": "picked_up"})
        self.client.post(self.status_url(), {"status": "out_for_delivery"})
        self.client.post(self.status_url(), {"status": "delivered"})

        profile = DeliveryPartnerProfile.objects.get(user=self.partner)
        self.assertEqual(profile.total_deliveries, 1)
        self.assertEqual(profile.total_earnings, self.restaurant.delivery_fee)


class DeliveryProfileAndEarningsTests(APITestCase):
    def setUp(self):
        self.partner = make_delivery_partner()

    def test_toggle_online_status(self):
        self.client.force_authenticate(user=self.partner)
        response = self.client.patch(reverse("deliveries:profile"), {"is_online": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_online"])

    def test_earnings_endpoint_returns_zero_state(self):
        self.client.force_authenticate(user=self.partner)
        response = self.client.get(reverse("deliveries:earnings"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_deliveries"], 0)
