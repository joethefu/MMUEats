from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from restaurants.models import Restaurant
from users.models import User

from .models import Category, Meal


def make_vendor_with_restaurant(email="vendor@x.com"):
    vendor = User.objects.create_user(email=email, password="Pass12345", full_name="Vendor", role=User.Role.VENDOR)
    vendor.is_approved = True
    vendor.is_email_verified = True
    vendor.save()
    restaurant = Restaurant.objects.create(owner=vendor, name="Test Kitchen", slug=f"kitchen-{vendor.id}", location="Loc", status="open", is_active=True)
    return vendor, restaurant


class MealTests(APITestCase):
    def setUp(self):
        self.vendor, self.restaurant = make_vendor_with_restaurant()
        self.category = Category.objects.create(name="Lunch", slug="lunch")

    def test_vendor_can_create_meal_for_own_restaurant(self):
        self.client.force_authenticate(user=self.vendor)
        url = reverse("meals:meal-list")
        response = self.client.post(url, {
            "name": "Chicken Rice", "category": self.category.id, "price": "250.00",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        meal = Meal.objects.get(name="Chicken Rice")
        self.assertEqual(meal.restaurant, self.restaurant)

    def test_discounted_price_calculation(self):
        meal = Meal.objects.create(restaurant=self.restaurant, name="Burger", price=Decimal("200.00"), discount_percentage=10)
        self.assertEqual(meal.discounted_price, Decimal("180.00"))

    def test_public_can_browse_meals(self):
        Meal.objects.create(restaurant=self.restaurant, name="Fries", price=Decimal("100.00"))
        url = reverse("meals:meal-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_search_meals_by_name(self):
        Meal.objects.create(restaurant=self.restaurant, name="Spicy Wings", price=Decimal("150.00"))
        Meal.objects.create(restaurant=self.restaurant, name="Plain Rice", price=Decimal("80.00"))
        url = reverse("meals:meal-list")
        response = self.client.get(url, {"search": "Spicy"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Spicy Wings")

    def test_vendor_cannot_create_meal_for_another_restaurant(self):
        other_vendor, other_restaurant = make_vendor_with_restaurant("other@x.com")
        self.client.force_authenticate(user=other_vendor)
        url = reverse("meals:meal-list")
        response = self.client.post(url, {"name": "Sneaky Meal", "price": "50.00"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        meal = Meal.objects.get(name="Sneaky Meal")
        # Created under the authenticated vendor's OWN restaurant, never an arbitrary one.
        self.assertEqual(meal.restaurant, other_restaurant)

    def test_unavailable_meal_hidden_from_public_listing(self):
        Meal.objects.create(restaurant=self.restaurant, name="Hidden", price=Decimal("50.00"), is_available=False)
        url = reverse("meals:meal-list")
        response = self.client.get(url)
        names = [m["name"] for m in response.data["results"]]
        self.assertNotIn("Hidden", names)
