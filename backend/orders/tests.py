from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from meals.models import Meal
from restaurants.models import Restaurant
from users.models import User

from .models import Cart, Order


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
        owner=vendor, name="Test Kitchen", slug=f"kitchen-{vendor.id}", location="Loc",
        status="open", is_active=True, delivery_fee=Decimal("50.00"),
    )
    return vendor, restaurant


class CartTests(APITestCase):
    def setUp(self):
        self.customer = make_customer()
        self.vendor, self.restaurant = make_vendor_with_restaurant()
        self.meal = Meal.objects.create(restaurant=self.restaurant, name="Ugali Beef", price=Decimal("300.00"))
        self.client.force_authenticate(user=self.customer)

    def test_add_item_to_cart(self):
        url = reverse("orders:cart")
        response = self.client.post(url, {"meal_id": str(self.meal.id), "quantity": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 2)

    def test_cannot_add_meals_from_two_restaurants(self):
        _, other_restaurant = make_vendor_with_restaurant("other@x.com")
        other_meal = Meal.objects.create(restaurant=other_restaurant, name="Pizza", price=Decimal("500.00"))

        url = reverse("orders:cart")
        self.client.post(url, {"meal_id": str(self.meal.id), "quantity": 1})
        response = self.client.post(url, {"meal_id": str(other_meal.id), "quantity": 1})
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_cannot_add_unavailable_meal(self):
        unavailable = Meal.objects.create(restaurant=self.restaurant, name="Gone", price=Decimal("100.00"), is_available=False)
        url = reverse("orders:cart")
        response = self.client.post(url, {"meal_id": str(unavailable.id), "quantity": 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_single_item_clears_restaurant_when_empty(self):
        url = reverse("orders:cart")
        add_resp = self.client.post(url, {"meal_id": str(self.meal.id), "quantity": 1})
        item_id = add_resp.data["items"][0]["id"]

        response = self.client.delete(url, {"item_id": item_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 0)
        self.assertIsNone(response.data["restaurant"])


class CheckoutTests(APITestCase):
    def setUp(self):
        self.customer = make_customer()
        self.vendor, self.restaurant = make_vendor_with_restaurant()
        self.meal = Meal.objects.create(restaurant=self.restaurant, name="Pilau", price=Decimal("250.00"), stock_quantity=5)
        self.client.force_authenticate(user=self.customer)
        self.client.post(reverse("orders:cart"), {"meal_id": str(self.meal.id), "quantity": 2})

    def test_checkout_creates_order_and_clears_cart(self):
        url = reverse("orders:checkout")
        response = self.client.post(url, {
            "delivery_campus_location": "Hostel C",
            "payment_method": "cash_on_delivery",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["subtotal"], "500.00")
        self.assertEqual(response.data["delivery_fee"], "50.00")
        self.assertEqual(response.data["total"], "550.00")
        self.assertEqual(response.data["status"], "pending")

        cart = Cart.objects.get(customer=self.customer)
        self.assertEqual(cart.items.count(), 0)

        self.meal.refresh_from_db()
        self.assertEqual(self.meal.stock_quantity, 3)  # decremented by ordered quantity
        self.assertEqual(self.meal.order_count, 2)

    def test_checkout_with_empty_cart_rejected(self):
        Cart.objects.filter(customer=self.customer).update()
        Cart.objects.get(customer=self.customer).items.all().delete()
        url = reverse("orders:checkout")
        response = self.client.post(url, {"delivery_campus_location": "Hostel A", "payment_method": "cash_on_delivery"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "empty_cart")

    def test_checkout_rejected_when_restaurant_closed(self):
        self.restaurant.status = "closed"
        self.restaurant.save()
        url = reverse("orders:checkout")
        response = self.client.post(url, {"delivery_campus_location": "Hostel A", "payment_method": "cash_on_delivery"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "restaurant_unavailable")


class OrderLifecycleTests(APITestCase):
    def setUp(self):
        self.customer = make_customer()
        self.vendor, self.restaurant = make_vendor_with_restaurant()
        self.meal = Meal.objects.create(restaurant=self.restaurant, name="Chapati Beans", price=Decimal("150.00"))

        self.client.force_authenticate(user=self.customer)
        self.client.post(reverse("orders:cart"), {"meal_id": str(self.meal.id), "quantity": 1})
        checkout_resp = self.client.post(reverse("orders:checkout"), {
            "delivery_campus_location": "Hostel D", "payment_method": "cash_on_delivery",
        })
        self.order_id = checkout_resp.data["id"]

    def test_customer_sees_own_order_vendor_sees_restaurant_order(self):
        response = self.client.get(reverse("orders:order-detail", args=[self.order_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        other_customer = make_customer("other@gmail.com")
        self.client.force_authenticate(user=other_customer)
        response = self.client.get(reverse("orders:order-detail", args=[self.order_id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # scoped queryset hides it

        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(reverse("orders:order-detail", args=[self.order_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_vendor_can_progress_order_through_valid_transitions(self):
        self.client.force_authenticate(user=self.vendor)
        url = reverse("orders:order-update-status", args=[self.order_id])

        for target in ["accepted", "preparing", "ready_for_pickup"]:
            response = self.client.post(url, {"status": target})
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            self.assertEqual(response.data["status"], target)

    def test_vendor_cannot_skip_statuses(self):
        self.client.force_authenticate(user=self.vendor)
        url = reverse("orders:order-update-status", args=[self.order_id])
        # 'ready_for_pickup' IS a vendor-permitted target status, but skipping straight
        # there from 'pending' violates the transition graph -> invalid_transition (400).
        response = self.client.post(url, {"status": "ready_for_pickup"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "invalid_transition")

    def test_vendor_cannot_set_delivery_partner_only_status(self):
        self.client.force_authenticate(user=self.vendor)
        url = reverse("orders:order-update-status", args=[self.order_id])
        # 'delivered' is never a vendor-permitted target status at all -> permission_denied (403).
        response = self.client.post(url, {"status": "delivered"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "permission_denied")

    def test_other_vendor_cannot_update_status(self):
        other_vendor, _ = make_vendor_with_restaurant("intruder@x.com")
        self.client.force_authenticate(user=other_vendor)
        url = reverse("orders:order-update-status", args=[self.order_id])
        response = self.client.post(url, {"status": "accepted"})
        # Queryset is scoped to the vendor's own restaurant, so an order belonging
        # to someone else's restaurant is invisible (404) rather than merely
        # forbidden (403) — this avoids leaking that the order exists at all.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_can_cancel_pending_order(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse("orders:order-cancel", args=[self.order_id])
        response = self.client.post(url, {"reason": "Changed my mind"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")

    def test_customer_cannot_cancel_after_preparation_begins(self):
        self.client.force_authenticate(user=self.vendor)
        status_url = reverse("orders:order-update-status", args=[self.order_id])
        self.client.post(status_url, {"status": "accepted"})
        self.client.post(status_url, {"status": "preparing"})

        self.client.force_authenticate(user=self.customer)
        cancel_url = reverse("orders:order-cancel", args=[self.order_id])
        response = self.client.post(cancel_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "too_late")

    def test_reorder_rebuilds_cart(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse("orders:order-reorder", args=[self.order_id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["meal_name"], "Chapati Beans")
