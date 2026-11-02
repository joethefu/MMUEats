"""
Cross-app coverage that doesn't naturally belong to any single app, per Phase 11's
testing pass (spec §66). Two kinds of test live here:

1. Gap-filling unit tests for things that were built but never got a dedicated
   test (favorites, saved delivery locations, order rejection, reviews).
2. One comprehensive integration test that drives a single order through every
   phase's machinery end-to-end in one continuous scenario — coupon pricing,
   M-Pesa payment, vendor acceptance, delivery-partner assignment and handoff,
   notifications firing at each step, and both review types — exactly the kind
   of cross-phase path that per-app test files can't naturally exercise.
"""

from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from deliveries.models import Delivery, DeliveryPartnerProfile
from meals.models import Meal
from notifications.models import Notification
from orders.models import Order
from payments.models import Payment
from promotions.models import Coupon
from restaurants.models import FavoriteRestaurant, Restaurant, RestaurantReview
from users.models import DeliveryLocation, User


def make_customer(email="cust@gmail.com"):
    user = User.objects.create_user(email=email, password="Pass12345", full_name="Customer")
    user.is_email_verified = True
    user.save()
    return user


def make_vendor_with_restaurant(email="vendor@x.com", delivery_fee=Decimal("50.00")):
    vendor = User.objects.create_user(email=email, password="Pass12345", full_name="Vendor", role=User.Role.VENDOR)
    vendor.is_approved = True
    vendor.is_email_verified = True
    vendor.save()
    restaurant = Restaurant.objects.create(
        owner=vendor, name="Integration Kitchen", slug=f"ik-{vendor.id}", location="Loc",
        status="open", is_active=True, delivery_fee=delivery_fee,
    )
    return vendor, restaurant


def make_delivery_partner(email="rider@x.com"):
    partner = User.objects.create_user(email=email, password="Pass12345", full_name="Rider", role=User.Role.DELIVERY_PARTNER)
    partner.is_approved = True
    partner.is_email_verified = True
    partner.save()
    return partner


class FavoritesCoverageTests(APITestCase):
    """Favorites had routing tests (Phase 4) but never a create/list/delete test."""

    def setUp(self):
        self.customer = make_customer()
        self.vendor, self.restaurant = make_vendor_with_restaurant()
        self.meal = Meal.objects.create(restaurant=self.restaurant, name="Fave Meal", price=Decimal("100.00"))
        self.client.force_authenticate(user=self.customer)

    def test_favorite_and_unfavorite_restaurant(self):
        create_resp = self.client.post(reverse("restaurants:favorite-restaurant-list"), {"restaurant": str(self.restaurant.id)})
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(FavoriteRestaurant.objects.filter(user=self.customer, restaurant=self.restaurant).exists())

        fav_id = create_resp.data["id"]
        delete_resp = self.client.delete(reverse("restaurants:favorite-restaurant-detail", args=[fav_id]))
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FavoriteRestaurant.objects.filter(user=self.customer, restaurant=self.restaurant).exists())

    def test_favoriting_same_restaurant_twice_does_not_duplicate(self):
        url = reverse("restaurants:favorite-restaurant-list")
        self.client.post(url, {"restaurant": str(self.restaurant.id)})
        self.client.post(url, {"restaurant": str(self.restaurant.id)})
        self.assertEqual(FavoriteRestaurant.objects.filter(user=self.customer, restaurant=self.restaurant).count(), 1)

    def test_favorite_meal(self):
        response = self.client.post(reverse("meals:favorite-meal-list"), {"meal": str(self.meal.id)})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        list_resp = self.client.get(reverse("meals:favorite-meal-list"))
        self.assertEqual(len(list_resp.data["results"]), 1)


class SavedDeliveryLocationTests(APITestCase):
    """DeliveryLocation (spec §21/§36: save multiple delivery locations) had zero test coverage."""

    def setUp(self):
        self.customer = make_customer()
        self.client.force_authenticate(user=self.customer)

    def test_create_and_list_saved_locations(self):
        url = reverse("users:delivery-location-list")
        response = self.client.post(url, {"label": "My Room", "campus_location": "Hostel C", "is_default": True})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        list_resp = self.client.get(url)
        self.assertEqual(len(list_resp.data["results"]), 1)

    def test_setting_new_default_unsets_previous_default(self):
        url = reverse("users:delivery-location-list")
        first = self.client.post(url, {"label": "A", "campus_location": "Hostel A", "is_default": True})
        second = self.client.post(url, {"label": "B", "campus_location": "Hostel B", "is_default": True})
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)

        first_loc = DeliveryLocation.objects.get(pk=first.data["id"])
        self.assertFalse(first_loc.is_default)

    def test_user_only_sees_own_locations(self):
        DeliveryLocation.objects.create(user=self.customer, label="Mine", campus_location="Hostel A")
        other = make_customer("other-loc@gmail.com")
        DeliveryLocation.objects.create(user=other, label="Theirs", campus_location="Hostel B")

        response = self.client.get(reverse("users:delivery-location-list"))
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["label"], "Mine")


class OrderRejectionTests(APITestCase):
    """Vendor rejection (spec §25/§39) — distinct from customer cancellation, never directly tested."""

    def test_vendor_can_reject_pending_order(self):
        customer = make_customer()
        vendor, restaurant = make_vendor_with_restaurant()
        meal = Meal.objects.create(restaurant=restaurant, name="Reject Meal", price=Decimal("100.00"))

        self.client.force_authenticate(user=customer)
        self.client.post(reverse("orders:cart"), {"meal_id": str(meal.id), "quantity": 1})
        checkout = self.client.post(reverse("orders:checkout"), {
            "delivery_campus_location": "Hostel A", "payment_method": "cash_on_delivery",
        })
        order_id = checkout.data["id"]

        self.client.force_authenticate(user=vendor)
        response = self.client.post(reverse("orders:order-update-status", args=[order_id]), {
            "status": "rejected", "reason": "Out of ingredients",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "rejected")
        self.assertEqual(response.data["cancellation_reason"], "Out of ingredients")

        order = Order.objects.get(pk=order_id)
        self.assertIsNotNone(order.cancelled_at)

        self.assertTrue(
            Notification.objects.filter(user=customer, notification_type=Notification.Type.ORDER_CANCELLED).exists()
        )


class FullOrderJourneyIntegrationTest(APITestCase):
    """
    The comprehensive cross-phase test: one order driven through coupon pricing
    (Ph10), M-Pesa mock payment (Ph7), vendor acceptance (Ph5), delivery-partner
    pool assignment and handoff (Ph6), real-time notification firing at each
    step (Ph8), and both review types (Ph4/6) — in one continuous scenario.
    """

    def test_full_order_journey_across_every_phase(self):
        customer = make_customer("journey@gmail.com")
        vendor, restaurant = make_vendor_with_restaurant("journey-vendor@x.com", delivery_fee=Decimal("60.00"))
        partner = make_delivery_partner("journey-rider@x.com")
        meal = Meal.objects.create(restaurant=restaurant, name="Journey Meal", price=Decimal("500.00"), stock_quantity=10)

        now = timezone.now()
        Coupon.objects.create(
            code="JOURNEY15", discount_type=Coupon.DiscountType.PERCENTAGE, discount_value=Decimal("15.00"),
            valid_from=now - timezone.timedelta(days=1), valid_until=now + timezone.timedelta(days=1), is_active=True,
        )

        # --- Customer: browse, favorite, cart, checkout with coupon + M-Pesa ---
        self.client.force_authenticate(user=customer)
        self.client.post(reverse("restaurants:favorite-restaurant-list"), {"restaurant": str(restaurant.id)})
        self.client.post(reverse("orders:cart"), {"meal_id": str(meal.id), "quantity": 1})

        checkout = self.client.post(reverse("orders:checkout"), {
            "delivery_campus_location": "Hostel A", "payment_method": "mpesa", "coupon_code": "journey15",
        })
        self.assertEqual(checkout.status_code, status.HTTP_201_CREATED, checkout.data)
        # 500 subtotal + 60 delivery - 15% of 500 (=75) = 485
        self.assertEqual(checkout.data["total"], "485.00")
        order_id = checkout.data["id"]

        # --- M-Pesa mock payment ---
        stk = self.client.post(reverse("payments:mpesa-stk-push"), {"order_id": order_id, "phone_number": "254712345678"})
        self.assertEqual(stk.status_code, status.HTTP_200_OK)
        self.assertTrue(stk.data["payment"]["is_mocked"])

        sim = self.client.post(reverse("payments:mpesa-simulate"), {"order_id": order_id, "success": True})
        self.assertEqual(sim.status_code, status.HTTP_200_OK)

        payment = Payment.objects.get(order_id=order_id)
        self.assertEqual(payment.status, Payment.Status.PAID)

        # --- Vendor: accept, prepare, mark ready ---
        self.client.force_authenticate(user=vendor)
        status_url = reverse("orders:order-update-status", args=[order_id])
        for target in ["accepted", "preparing", "ready_for_pickup"]:
            resp = self.client.post(status_url, {"status": target})
            self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

        self.assertTrue(
            Notification.objects.filter(user=customer, notification_type=Notification.Type.ORDER_ACCEPTED).exists()
        )

        # --- Delivery partner: accept from pool, pick up, deliver ---
        delivery = Delivery.objects.get(order_id=order_id)
        self.client.force_authenticate(user=partner)
        accept_resp = self.client.post(reverse("deliveries:my-delivery-accept", args=[delivery.pk]))
        self.assertEqual(accept_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Notification.objects.filter(user=customer, notification_type=Notification.Type.DELIVERY_PARTNER_ASSIGNED).exists()
        )

        for target in ["picked_up", "out_for_delivery", "delivered"]:
            resp = self.client.post(status_url, {"status": target})
            self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

        order = Order.objects.get(pk=order_id)
        self.assertEqual(order.status, "delivered")
        self.assertEqual(order.payment_status, "paid")  # was already paid via M-Pesa before delivery

        delivery.refresh_from_db()
        self.assertEqual(delivery.earnings, Decimal("60.00"))
        profile = DeliveryPartnerProfile.objects.get(user=partner)
        self.assertEqual(profile.total_deliveries, 1)

        # --- Customer: leave both review types ---
        self.client.force_authenticate(user=customer)
        restaurant_review = self.client.post(reverse("restaurants:restaurant-review-list"), {
            "restaurant": str(restaurant.id), "order": order_id, "rating": 5, "comment": "Excellent!",
        })
        self.assertEqual(restaurant_review.status_code, status.HTTP_201_CREATED, restaurant_review.data)

        delivery_review = self.client.post(reverse("deliveries:delivery-review-list"), {
            "delivery": str(delivery.pk), "speed_rating": 4, "comment": "Quick delivery",
        })
        self.assertEqual(delivery_review.status_code, status.HTTP_201_CREATED, delivery_review.data)

        restaurant.refresh_from_db()
        self.assertEqual(restaurant.average_rating, Decimal("5.00"))
        profile.refresh_from_db()
        self.assertEqual(profile.average_rating, Decimal("4.00"))

        # --- Final sanity: order visible in customer's history, payment in their history ---
        history = self.client.get(reverse("orders:order-list"))
        self.assertEqual(history.data["count"], 1)
        payment_history = self.client.get(reverse("payments:my-payment-list"))
        self.assertEqual(payment_history.data["count"], 1)
