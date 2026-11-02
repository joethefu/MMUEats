from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from meals.models import Meal
from orders.models import Cart, Order
from restaurants.models import Restaurant
from users.models import User


def make_vendor_with_restaurant(email="vendor@x.com"):
    vendor = User.objects.create_user(email=email, password="Pass12345", full_name="Vendor", role=User.Role.VENDOR)
    vendor.is_approved = True
    vendor.is_email_verified = True
    vendor.save()
    restaurant = Restaurant.objects.create(
        owner=vendor, name="Dash Kitchen", slug=f"dash-{vendor.id}", location="Loc",
        status="open", is_active=True, delivery_fee=Decimal("50.00"),
    )
    return vendor, restaurant


def make_customer(email="cust@gmail.com"):
    user = User.objects.create_user(email=email, password="Pass12345", full_name="Customer")
    user.is_email_verified = True
    user.save()
    return user


class AdminDashboardTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="platform-admin@mmueats.com", password="AdminPass123")

    def test_customer_cannot_access_admin_dashboard(self):
        customer = make_customer()
        self.client.force_authenticate(user=customer)
        response = self.client.get(reverse("analytics:admin-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_dashboard_reflects_platform_state(self):
        vendor, restaurant = make_vendor_with_restaurant("dashvendor@x.com")
        customer = make_customer("dashcust@gmail.com")
        Order.objects.create(
            customer=customer, restaurant=restaurant, delivery_campus_location="Hostel A",
            subtotal=Decimal("300.00"), delivery_fee=Decimal("50.00"), total=Decimal("350.00"),
            status=Order.Status.DELIVERED,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("analytics:admin-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_orders"], 1)
        self.assertEqual(response.data["completed_orders"], 1)
        self.assertEqual(Decimal(str(response.data["total_revenue"])), Decimal("350.00"))
        self.assertGreaterEqual(response.data["total_users"], 1)


class AdminUserManagementTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="usermgmt-admin@mmueats.com", password="AdminPass123")

    def test_admin_can_list_users_filtered_by_role(self):
        make_customer("filtertest@gmail.com")
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("analytics:admin-user-list"), {"role": "customer"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(u["role"] == "customer" for u in response.data["results"]))

    def test_admin_can_suspend_and_reactivate_user(self):
        customer = make_customer("suspend-me@gmail.com")
        self.client.force_authenticate(user=self.admin)

        suspend_resp = self.client.post(reverse("analytics:admin-user-suspend", args=[customer.id]))
        self.assertEqual(suspend_resp.status_code, status.HTTP_200_OK)
        customer.refresh_from_db()
        self.assertTrue(customer.is_suspended)

        reactivate_resp = self.client.post(reverse("analytics:admin-user-reactivate", args=[customer.id]))
        self.assertEqual(reactivate_resp.status_code, status.HTTP_200_OK)
        customer.refresh_from_db()
        self.assertFalse(customer.is_suspended)

    def test_suspended_user_cannot_login(self):
        customer = make_customer("gets-suspended@gmail.com")
        self.client.force_authenticate(user=self.admin)
        self.client.post(reverse("analytics:admin-user-suspend", args=[customer.id]))

        self.client.force_authenticate(user=None)
        login_resp = self.client.post(reverse("authentication:login"), {
            "email": "gets-suspended@gmail.com", "password": "Pass12345",
        })
        self.assertEqual(login_resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_admin_cannot_suspend_users(self):
        customer = make_customer()
        target = make_customer("target@gmail.com")
        self.client.force_authenticate(user=customer)
        response = self.client.post(reverse("analytics:admin-user-suspend", args=[target.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AuditLogTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="audit-admin@mmueats.com", password="AdminPass123")

    def test_admin_can_view_audit_logs(self):
        customer = make_customer("audited@gmail.com")
        self.client.force_authenticate(user=self.admin)
        self.client.post(reverse("analytics:admin-user-suspend", args=[customer.id]))

        response = self.client.get(reverse("analytics:admin-audit-logs"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(log["action"] == "user_suspended" for log in response.data))

    def test_non_admin_cannot_view_audit_logs(self):
        customer = make_customer()
        self.client.force_authenticate(user=customer)
        response = self.client.get(reverse("analytics:admin-audit-logs"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class VendorDashboardTests(APITestCase):
    def setUp(self):
        self.vendor, self.restaurant = make_vendor_with_restaurant()
        self.customer = make_customer()
        self.meal = Meal.objects.create(restaurant=self.restaurant, name="Nyama Choma", price=Decimal("400.00"))

    def test_vendor_without_restaurant_gets_404(self):
        lonely_vendor = User.objects.create_user(
            email="lonely@x.com", password="Pass12345", full_name="Lonely", role=User.Role.VENDOR
        )
        lonely_vendor.is_approved = True
        lonely_vendor.save()
        self.client.force_authenticate(user=lonely_vendor)
        response = self.client.get(reverse("analytics:vendor-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_dashboard_reflects_delivered_order_revenue(self):
        order = Order.objects.create(
            customer=self.customer, restaurant=self.restaurant, delivery_campus_location="Hostel A",
            subtotal=Decimal("400.00"), delivery_fee=Decimal("50.00"), total=Decimal("450.00"),
            status=Order.Status.DELIVERED,
        )
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(reverse("analytics:vendor-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["completed_orders_count"], 1)
        self.assertEqual(Decimal(str(response.data["today_revenue"])), Decimal("450.00"))

    def test_customer_cannot_access_vendor_dashboard(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(reverse("analytics:vendor-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sales_report_aggregates_revenue(self):
        Order.objects.create(
            customer=self.customer, restaurant=self.restaurant, delivery_campus_location="Hostel B",
            subtotal=Decimal("400.00"), delivery_fee=Decimal("50.00"), total=Decimal("450.00"),
            status=Order.Status.DELIVERED,
        )
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(reverse("analytics:vendor-sales-report"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_orders"], 1)
        self.assertEqual(Decimal(str(response.data["total_revenue"])), Decimal("450.00"))
