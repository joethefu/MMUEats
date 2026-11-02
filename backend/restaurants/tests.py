from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import Restaurant


def make_vendor(email="vendor@grill.com"):
    user = User.objects.create_user(email=email, password="Pass12345", full_name="Vendor Owner", role=User.Role.VENDOR)
    user.is_approved = True
    user.is_email_verified = True
    user.save()
    return user


def make_customer(email="cust@gmail.com"):
    user = User.objects.create_user(email=email, password="Pass12345", full_name="Customer")
    user.is_email_verified = True
    user.save()
    return user


class RestaurantTests(APITestCase):
    def test_vendor_can_create_restaurant(self):
        vendor = make_vendor()
        self.client.force_authenticate(user=vendor)
        url = reverse("restaurants:restaurant-list")
        response = self.client.post(url, {
            "name": "Campus Grill", "location": "Near Main Gate", "delivery_fee": "50.00",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Restaurant.objects.filter(owner=vendor).exists())

    def test_vendor_cannot_create_second_restaurant(self):
        vendor = make_vendor()
        Restaurant.objects.create(owner=vendor, name="First", slug="first", location="Loc")
        self.client.force_authenticate(user=vendor)
        url = reverse("restaurants:restaurant-list")
        response = self.client.post(url, {"name": "Second", "location": "Loc2"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_cannot_create_restaurant(self):
        customer = make_customer()
        self.client.force_authenticate(user=customer)
        url = reverse("restaurants:restaurant-list")
        response = self.client.post(url, {"name": "Nope", "location": "Loc"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anyone_can_list_active_restaurants(self):
        vendor = make_vendor()
        Restaurant.objects.create(owner=vendor, name="Open Place", slug="open-place", location="Loc", status="open", is_active=True)
        url = reverse("restaurants:restaurant-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_favorites_specific_route_not_shadowed_by_slug_detail(self):
        """Regression test for the router-ordering bug fixed during Phase 4."""
        customer = make_customer()
        self.client.force_authenticate(user=customer)
        url = reverse("restaurants:favorite-restaurant-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    def test_vendor_can_update_only_own_restaurant(self):
        vendor1 = make_vendor("v1@x.com")
        vendor2 = make_vendor("v2@x.com")
        r1 = Restaurant.objects.create(owner=vendor1, name="R1", slug="r1", location="Loc")
        self.client.force_authenticate(user=vendor2)
        url = reverse("restaurants:restaurant-detail", args=[r1.slug])
        response = self.client.patch(url, {"name": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # scoped queryset hides it
