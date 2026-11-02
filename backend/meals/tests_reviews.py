import io
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from meals.models import FavoriteMeal, Meal, MealReview
from orders.tests import make_customer, make_vendor_with_restaurant


def png_file(name="a.png", size=(60, 60)):
    buf = io.BytesIO()
    Image.new("RGB", size, "red").save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


class MealReviewTests(APITestCase):
    def setUp(self):
        self.customer = make_customer()
        self.other = make_customer("other@gmail.com")
        _, self.restaurant = make_vendor_with_restaurant()
        self.meal = Meal.objects.create(restaurant=self.restaurant, name="Pilau", price=Decimal("250"))
        self.url = reverse("meals:meal-review-list")

    def test_rating_review_and_aggregate(self):
        self.client.force_authenticate(self.customer)
        r = self.client.post(self.url, {"meal": str(self.meal.id), "rating": 5, "comment": "Great"})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.other)
        self.client.post(self.url, {"meal": str(self.meal.id), "rating": 3})
        self.meal.refresh_from_db()
        self.assertEqual(self.meal.ratings_count, 2)
        self.assertEqual(self.meal.average_rating, Decimal("4.00"))

    def test_reposting_updates_instead_of_duplicating(self):
        self.client.force_authenticate(self.customer)
        self.client.post(self.url, {"meal": str(self.meal.id), "rating": 2})
        self.client.post(self.url, {"meal": str(self.meal.id), "rating": 4, "comment": "Better now"})
        self.assertEqual(MealReview.objects.filter(meal=self.meal).count(), 1)
        self.meal.refresh_from_db()
        self.assertEqual(self.meal.average_rating, Decimal("4.00"))

    def test_rating_out_of_range_rejected(self):
        self.client.force_authenticate(self.customer)
        for bad in (0, 6):
            r = self.client.post(self.url, {"meal": str(self.meal.id), "rating": bad})
            self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_can_read_but_not_write(self):
        self.assertEqual(self.client.get(self.url, {"meal": str(self.meal.id)}).status_code, 200)
        self.assertIn(self.client.post(self.url, {"meal": str(self.meal.id), "rating": 5}).status_code, (401, 403))

    def test_delete_only_own_review(self):
        self.client.force_authenticate(self.customer)
        rid = self.client.post(self.url, {"meal": str(self.meal.id), "rating": 5}).data["id"]
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.delete(reverse("meals:meal-review-detail", args=[rid])).status_code, 404)
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.delete(reverse("meals:meal-review-detail", args=[rid])).status_code, 204)
        self.meal.refresh_from_db()
        self.assertEqual(self.meal.ratings_count, 0)

    def test_favorite_id_exposed_and_user_scoped(self):
        self.client.force_authenticate(self.customer)
        fav = self.client.post(reverse("meals:favorite-meal-list"), {"meal": str(self.meal.id)})
        self.assertEqual(fav.status_code, 201)
        listing = self.client.get(reverse("meals:meal-list")).data["results"][0]
        self.assertTrue(listing["is_favorited"])
        self.assertEqual(listing["favorite_id"], fav.data["id"])
        self.client.force_authenticate(self.other)
        self.assertFalse(self.client.get(reverse("meals:meal-list")).data["results"][0]["is_favorited"])
        self.client.force_authenticate(self.customer)
        self.client.delete(reverse("meals:favorite-meal-detail", args=[fav.data["id"]]))
        self.assertEqual(FavoriteMeal.objects.count(), 0)

    def test_search_finds_meal_by_name(self):
        r = self.client.get(reverse("meals:meal-list"), {"search": "pila"})
        self.assertEqual(r.data["count"], 1)


class RestaurantRatingTests(APITestCase):
    def test_general_rating_upserts(self):
        customer = make_customer()
        _, restaurant = make_vendor_with_restaurant()
        self.client.force_authenticate(customer)
        url = reverse("restaurants:restaurant-review-list")
        self.client.post(url, {"restaurant": str(restaurant.id), "rating": 2})
        self.client.post(url, {"restaurant": str(restaurant.id), "rating": 5, "comment": "Loved it"})
        restaurant.refresh_from_db()
        self.assertEqual(restaurant.ratings_count, 1)
        self.assertEqual(restaurant.average_rating, Decimal("5.00"))


@override_settings(MEDIA_ROOT="/tmp/mmueats_test_media")
class ProfilePictureTests(APITestCase):
    def setUp(self):
        self.user = make_customer()
        self.client.force_authenticate(self.user)
        self.url = reverse("users:me")

    def test_multipart_upload_saves_file(self):
        r = self.client.patch(self.url, {"profile_picture": png_file()}, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(r.data["profile_picture"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_picture.name.startswith("profile_pictures/"))

    def test_json_body_with_non_file_gives_the_original_error(self):
        r = self.client.patch(self.url, {"profile_picture": "abc"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_non_image_rejected(self):
        bad = SimpleUploadedFile("a.txt", b"hello", content_type="text/plain")
        r = self.client.patch(self.url, {"profile_picture": bad}, format="multipart")
        self.assertEqual(r.status_code, 400)

    def test_delete_picture(self):
        self.client.patch(self.url, {"profile_picture": png_file()}, format="multipart")
        r = self.client.delete(reverse("users:me-profile-picture"))
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.data["profile_picture"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile_picture)


class PasswordChangeLogoutTests(APITestCase):
    def test_change_password_blacklists_sessions(self):
        user = make_customer()
        refresh = RefreshToken.for_user(user)
        self.client.force_authenticate(user)
        r = self.client.post(reverse("authentication:change-password"), {
            "old_password": "Pass12345", "new_password": "Brand-new-9Pass", "confirm_password": "Brand-new-9Pass",
        })
        self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(r.data["logout_required"])
        self.client.force_authenticate(None)
        again = self.client.post(reverse("authentication:token-refresh"), {"refresh": str(refresh)})
        self.assertEqual(again.status_code, 401)
