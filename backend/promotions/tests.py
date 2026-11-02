from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from meals.models import Meal
from restaurants.models import Restaurant
from users.models import User

from .models import Coupon, CouponRedemption


def make_admin(email="admin@mmueats.com"):
    return User.objects.create_superuser(email=email, password="AdminPass123")


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
        owner=vendor, name="Promo Kitchen", slug=f"promo-{vendor.id}", location="Loc",
        status="open", is_active=True, delivery_fee=Decimal("50.00"),
    )
    return vendor, restaurant


def make_coupon(**overrides):
    now = timezone.now()
    defaults = {
        "code": "SAVE10", "discount_type": Coupon.DiscountType.PERCENTAGE, "discount_value": Decimal("10.00"),
        "valid_from": now - timezone.timedelta(days=1), "valid_until": now + timezone.timedelta(days=10),
        "is_active": True,
    }
    defaults.update(overrides)
    return Coupon.objects.create(**defaults)


class CouponComputationTests(APITestCase):
    def test_percentage_discount_capped(self):
        coupon = make_coupon(discount_type=Coupon.DiscountType.PERCENTAGE, discount_value=Decimal("50.00"), max_discount_amount=Decimal("30.00"))
        amount, free_delivery = coupon.compute_discount(Decimal("200.00"), Decimal("50.00"))
        self.assertEqual(amount, Decimal("30.00"))  # 50% of 200 = 100, capped at 30
        self.assertFalse(free_delivery)

    def test_fixed_amount_discount_never_exceeds_subtotal(self):
        coupon = make_coupon(discount_type=Coupon.DiscountType.FIXED_AMOUNT, discount_value=Decimal("500.00"))
        amount, _ = coupon.compute_discount(Decimal("100.00"), Decimal("50.00"))
        self.assertEqual(amount, Decimal("100.00"))

    def test_free_delivery_type(self):
        coupon = make_coupon(discount_type=Coupon.DiscountType.FREE_DELIVERY)
        amount, free_delivery = coupon.compute_discount(Decimal("200.00"), Decimal("50.00"))
        self.assertEqual(amount, Decimal("0.00"))
        self.assertTrue(free_delivery)

    def test_is_currently_valid_respects_dates_and_active_flag(self):
        now = timezone.now()
        expired = make_coupon(code="EXPIRED", valid_from=now - timezone.timedelta(days=10), valid_until=now - timezone.timedelta(days=1))
        self.assertFalse(expired.is_currently_valid)

        inactive = make_coupon(code="INACTIVE", is_active=False)
        self.assertFalse(inactive.is_currently_valid)

        maxed_out = make_coupon(code="MAXED", max_uses=1, used_count=1)
        self.assertFalse(maxed_out.is_currently_valid)


class CouponCheckoutIntegrationTests(APITestCase):
    def setUp(self):
        self.customer = make_customer()
        self.vendor, self.restaurant = make_vendor_with_restaurant()
        self.meal = Meal.objects.create(restaurant=self.restaurant, name="Coupon Meal", price=Decimal("400.00"))
        self.client.force_authenticate(user=self.customer)
        self.client.post(reverse("orders:cart"), {"meal_id": str(self.meal.id), "quantity": 1})

    def test_checkout_with_valid_coupon_reduces_total(self):
        make_coupon(discount_type=Coupon.DiscountType.PERCENTAGE, discount_value=Decimal("10.00"))
        response = self.client.post(reverse("orders:checkout"), {
            "delivery_campus_location": "Hostel A", "payment_method": "cash_on_delivery", "coupon_code": "save10",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        # subtotal 400 + delivery 50 - 10% of 400 (=40) = 410
        self.assertEqual(response.data["discount_amount"], "40.00")
        self.assertEqual(response.data["total"], "410.00")
        self.assertTrue(CouponRedemption.objects.filter(customer=self.customer).exists())

    def test_checkout_with_invalid_coupon_rejected_and_cart_untouched(self):
        response = self.client.post(reverse("orders:checkout"), {
            "delivery_campus_location": "Hostel A", "payment_method": "cash_on_delivery", "coupon_code": "NOTREAL",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "invalid_code")

        # Cart should still have the item — checkout must not have partially completed.
        cart_response = self.client.get(reverse("orders:cart"))
        self.assertEqual(len(cart_response.data["items"]), 1)

    def test_free_delivery_coupon_zeroes_delivery_fee(self):
        make_coupon(code="FREESHIP", discount_type=Coupon.DiscountType.FREE_DELIVERY)
        response = self.client.post(reverse("orders:checkout"), {
            "delivery_campus_location": "Hostel A", "payment_method": "cash_on_delivery", "coupon_code": "FREESHIP",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["delivery_fee"], "0.00")
        self.assertEqual(response.data["total"], "400.00")

    def test_coupon_cannot_be_reused_beyond_per_customer_limit(self):
        make_coupon(code="ONCEONLY", max_uses_per_customer=1)
        first = self.client.post(reverse("orders:checkout"), {
            "delivery_campus_location": "Hostel A", "payment_method": "cash_on_delivery", "coupon_code": "ONCEONLY",
        })
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        self.client.post(reverse("orders:cart"), {"meal_id": str(self.meal.id), "quantity": 1})
        second = self.client.post(reverse("orders:checkout"), {
            "delivery_campus_location": "Hostel A", "payment_method": "cash_on_delivery", "coupon_code": "ONCEONLY",
        })
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(second.data["error"]["code"], "already_used")

    def test_coupon_scoped_to_different_restaurant_rejected(self):
        _, other_restaurant = make_vendor_with_restaurant("other@x.com")
        make_coupon(code="OTHERONLY", restaurant=other_restaurant)
        response = self.client.post(reverse("orders:checkout"), {
            "delivery_campus_location": "Hostel A", "payment_method": "cash_on_delivery", "coupon_code": "OTHERONLY",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "wrong_restaurant")

    def test_minimum_order_amount_enforced(self):
        make_coupon(code="BIGORDER", min_order_amount=Decimal("1000.00"))
        response = self.client.post(reverse("orders:checkout"), {
            "delivery_campus_location": "Hostel A", "payment_method": "cash_on_delivery", "coupon_code": "BIGORDER",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "minimum_not_met")


class ValidateCouponEndpointTests(APITestCase):
    def setUp(self):
        self.customer = make_customer()
        self.vendor, self.restaurant = make_vendor_with_restaurant()

    def test_validate_endpoint_previews_without_redeeming(self):
        make_coupon()
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(reverse("promotions:validate-coupon"), {
            "code": "SAVE10", "restaurant_id": str(self.restaurant.id), "subtotal": "400.00", "delivery_fee": "50.00",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["discount_amount"], Decimal("40.00"))
        self.assertEqual(CouponRedemption.objects.count(), 0)  # preview only


class CouponAdminCRUDTests(APITestCase):
    def test_admin_can_create_coupon(self):
        admin = make_admin()
        self.client.force_authenticate(user=admin)
        now = timezone.now()
        response = self.client.post(reverse("promotions:coupon-list"), {
            "code": "welcome20",
            "discount_type": "percentage",
            "discount_value": "20.00",
            "valid_from": now.isoformat(),
            "valid_until": (now + timezone.timedelta(days=30)).isoformat(),
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Coupon.objects.get().code, "WELCOME20")  # normalized uppercase

    def test_customer_cannot_manage_coupons(self):
        customer = make_customer()
        self.client.force_authenticate(user=customer)
        response = self.client.get(reverse("promotions:coupon-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
