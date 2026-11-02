from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import Advertisement, AdvertisementClick, AdvertisementImpression


def make_admin(email="admin@mmueats.com"):
    return User.objects.create_superuser(email=email, password="AdminPass123")


def make_customer(email="cust@gmail.com"):
    user = User.objects.create_user(email=email, password="Pass12345", full_name="Customer")
    user.is_email_verified = True
    user.save()
    return user


class AdvertisementAdminCRUDTests(APITestCase):
    def setUp(self):
        self.admin = make_admin()

    def test_admin_can_create_advertisement(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_authenticate(user=self.admin)
        today = timezone.localdate()
        tiny_gif = SimpleUploadedFile(
            "ad.gif", b"GIF87a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )
        response = self.client.post(reverse("advertisements:advertisement-list"), {
            "title": "Back to School Offer",
            "image": tiny_gif,
            "external_url": "https://example.com/promo",
            "placement": "startup_popup",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=7)).isoformat(),
            "priority": 5,
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Advertisement.objects.filter(title="Back to School Offer").exists())

    def test_multipart_create_omitting_is_active_defaults_to_true(self):
        """
        Regression test: DRF's BooleanField historically treats a missing key in
        multipart data as an HTML-checkbox 'unchecked' (False), silently
        overriding the model's default=True. Caught via manual curl testing —
        see ExplicitBooleanField in serializers.py for the fix.
        """
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_authenticate(user=self.admin)
        today = timezone.localdate()
        tiny_gif = SimpleUploadedFile(
            "ad2.gif", b"GIF87a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )
        response = self.client.post(reverse("advertisements:advertisement-list"), {
            "title": "No Explicit Active Flag",
            "image": tiny_gif,
            "external_url": "https://example.com/promo2",
            "placement": "startup_popup",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=7)).isoformat(),
            # is_active deliberately omitted
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        ad = Advertisement.objects.get(title="No Explicit Active Flag")
        self.assertTrue(ad.is_active)

    def test_customer_cannot_create_advertisement(self):
        customer = make_customer()
        self.client.force_authenticate(user=customer)
        response = self.client.post(reverse("advertisements:advertisement-list"), {"title": "Nope"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_cannot_list_all_advertisements(self):
        """Only /active/ is public — the admin list exposes scheduling/analytics data."""
        customer = make_customer()
        self.client.force_authenticate(user=customer)
        response = self.client.get(reverse("advertisements:advertisement-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ActiveAdvertisementScheduleTests(APITestCase):
    def setUp(self):
        self.admin = make_admin()
        self.today = timezone.localdate()

    def _create(self, **overrides):
        defaults = {
            "title": "Ad", "external_url": "https://example.com", "placement": "startup_popup",
            "start_date": self.today, "end_date": self.today, "is_active": True, "priority": 0,
            "created_by": self.admin,
        }
        defaults.update(overrides)
        return Advertisement.objects.create(**{k: v for k, v in defaults.items() if k != "image"})

    def test_active_endpoint_returns_only_currently_valid_ads(self):
        current = self._create(title="Current")
        self._create(title="Expired", start_date=self.today - timedelta(days=10), end_date=self.today - timedelta(days=1))
        self._create(title="Future", start_date=self.today + timedelta(days=1), end_date=self.today + timedelta(days=5))
        self._create(title="Inactive", is_active=False)

        response = self.client.get(reverse("advertisements:active"), {"placement": "startup_popup"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [ad["title"] for ad in response.data]
        self.assertEqual(titles, ["Current"])

    def test_active_endpoint_orders_by_priority(self):
        self._create(title="Low priority", priority=1)
        self._create(title="High priority", priority=10)

        response = self.client.get(reverse("advertisements:active"), {"placement": "startup_popup"})
        titles = [ad["title"] for ad in response.data]
        self.assertEqual(titles, ["High priority", "Low priority"])

    def test_active_endpoint_filters_by_placement(self):
        self._create(title="Popup ad", placement="startup_popup")
        self._create(title="Banner ad", placement="homepage_banner")

        response = self.client.get(reverse("advertisements:active"), {"placement": "homepage_banner"})
        titles = [ad["title"] for ad in response.data]
        self.assertEqual(titles, ["Banner ad"])

    def test_is_currently_valid_property(self):
        current = self._create(title="Valid")
        self.assertTrue(current.is_currently_valid)

        expired = self._create(title="Expired", start_date=self.today - timedelta(days=5), end_date=self.today - timedelta(days=1))
        self.assertFalse(expired.is_currently_valid)


class AdvertisementTrackingTests(APITestCase):
    def setUp(self):
        self.admin = make_admin()
        today = timezone.localdate()
        self.ad = Advertisement.objects.create(
            title="Trackable Ad", external_url="https://example.com/deal", placement="startup_popup",
            start_date=today, end_date=today, is_active=True, created_by=self.admin,
        )

    def test_anonymous_impression_recorded_with_device_id_only(self):
        url = reverse("advertisements:impression", args=[self.ad.id])
        response = self.client.post(url, {"device_id": "anon-device-123", "platform": "web"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        impression = AdvertisementImpression.objects.get(advertisement=self.ad)
        self.assertIsNone(impression.user)
        self.assertEqual(impression.device_id, "anon-device-123")

    def test_authenticated_click_records_user_and_returns_destination(self):
        customer = make_customer()
        self.client.force_authenticate(user=customer)
        url = reverse("advertisements:click", args=[self.ad.id])
        response = self.client.post(url, {"platform": "web"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["destination_url"], "https://example.com/deal")

        click = AdvertisementClick.objects.get(advertisement=self.ad)
        self.assertEqual(click.user, customer)

    def test_tracking_nonexistent_ad_returns_404(self):
        import uuid
        url = reverse("advertisements:impression", args=[uuid.uuid4()])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdvertisementAnalyticsTests(APITestCase):
    def setUp(self):
        self.admin = make_admin()
        today = timezone.localdate()
        self.ad = Advertisement.objects.create(
            title="Analytics Ad", external_url="https://example.com", placement="startup_popup",
            start_date=today, end_date=today, is_active=True, created_by=self.admin,
        )

    def test_ctr_calculation(self):
        for _ in range(10):
            AdvertisementImpression.objects.create(advertisement=self.ad, device_id="d")
        for _ in range(3):
            AdvertisementClick.objects.create(advertisement=self.ad, device_id="d", destination_url="https://example.com")

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("advertisements:advertisement-analytics", args=[self.ad.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["impressions"], 10)
        self.assertEqual(response.data["clicks"], 3)
        self.assertEqual(response.data["ctr_percent"], 30.0)

    def test_ctr_is_zero_with_no_impressions(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("advertisements:advertisement-analytics", args=[self.ad.id]))
        self.assertEqual(response.data["ctr_percent"], 0)
