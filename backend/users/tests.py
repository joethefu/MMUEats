from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import DeliveryPartnerApplication, User, VendorApplication


class VendorApplicationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin@mmueats.com", password="AdminPass123")

    def test_anyone_can_submit_vendor_application(self):
        url = reverse("users:vendor-application-list")
        payload = {
            "business_name": "Campus Bites",
            "owner_name": "Mary Njeri",
            "email": "mary@campusbites.com",
            "phone_number": "+254711223344",
            "business_location": "Near Main Gate",
            "food_categories": "Fast Food",
            "description": "Quick campus meals",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VendorApplication.objects.count(), 1)
        app = VendorApplication.objects.get()
        self.assertEqual(app.status, "pending")

    def test_non_admin_cannot_list_applications(self):
        VendorApplication.objects.create(
            business_name="X", owner_name="Y", email="x@y.com",
            phone_number="+254700000001", business_location="Loc",
        )
        customer = User.objects.create_user(email="cust@gmail.com", password="Pass12345", full_name="Cust")
        customer.is_email_verified = True
        customer.save()
        self.client.force_authenticate(user=customer)

        response = self.client.get(reverse("users:vendor-application-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_approve_vendor_application_creating_user(self):
        app = VendorApplication.objects.create(
            business_name="Campus Grill", owner_name="Peter Kamau", email="peter@grill.com",
            phone_number="+254722334455", business_location="Hostel B area",
        )
        self.client.force_authenticate(user=self.admin)

        url = reverse("users:vendor-application-review", args=[app.pk])
        response = self.client.post(url, {"action": "approve", "notes": "Looks good"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        app.refresh_from_db()
        self.assertEqual(app.status, "approved")
        self.assertIsNotNone(app.resulting_user)

        user = User.objects.get(email="peter@grill.com")
        self.assertEqual(user.role, User.Role.VENDOR)
        self.assertTrue(user.is_approved)
        self.assertTrue(user.is_email_verified)
        self.assertFalse(user.has_usable_password())  # must set password via emailed link

        self.assertTrue(any("approved" in m.subject.lower() for m in mail.outbox))

    def test_admin_can_reject_vendor_application(self):
        app = VendorApplication.objects.create(
            business_name="Sketchy Foods", owner_name="Nobody", email="nobody@x.com",
            phone_number="+254700000002", business_location="Unknown",
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:vendor-application-review", args=[app.pk])
        response = self.client.post(url, {"action": "reject", "notes": "Missing business registration"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        app.refresh_from_db()
        self.assertEqual(app.status, "rejected")
        self.assertIsNone(app.resulting_user)
        self.assertFalse(User.objects.filter(email="nobody@x.com").exists())

    def test_cannot_reapprove_already_approved_application(self):
        app = VendorApplication.objects.create(
            business_name="Twice", owner_name="Owner", email="twice@x.com",
            phone_number="+254700000003", business_location="Loc",
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:vendor-application-review", args=[app.pk])
        self.client.post(url, {"action": "approve"})
        second_response = self.client.post(url, {"action": "approve"})
        self.assertEqual(second_response.status_code, status.HTTP_409_CONFLICT)


class DeliveryPartnerApplicationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin2@mmueats.com", password="AdminPass123")

    def test_anyone_can_submit_delivery_application(self):
        url = reverse("users:delivery-partner-application-list")
        payload = {
            "full_name": "Brian Otieno",
            "email": "brian@gmail.com",
            "phone_number": "+254733445566",
            "preferred_area": "Hostel A - D",
            "availability": "Evenings",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DeliveryPartnerApplication.objects.count(), 1)

    def test_admin_approval_creates_delivery_partner_user(self):
        app = DeliveryPartnerApplication.objects.create(
            full_name="Grace Wambui", email="grace@gmail.com",
            phone_number="+254744556677", preferred_area="Library area",
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:delivery-partner-application-review", args=[app.pk])
        response = self.client.post(url, {"action": "approve"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = User.objects.get(email="grace@gmail.com")
        self.assertEqual(user.role, User.Role.DELIVERY_PARTNER)
        self.assertTrue(user.is_approved)

    def test_only_approved_delivery_partners_pass_role_permission(self):
        from common.permissions import IsDeliveryPartner
        from rest_framework.test import APIRequestFactory

        unapproved = User.objects.create_user(
            email="pending@gmail.com", password="Pass12345", full_name="Pending Rider",
            role=User.Role.DELIVERY_PARTNER,
        )
        self.assertFalse(unapproved.is_approved)  # save() override should have set this

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = unapproved
        self.assertFalse(IsDeliveryPartner().has_permission(request, None))

        unapproved.is_approved = True
        unapproved.save()
        request.user = unapproved
        self.assertTrue(IsDeliveryPartner().has_permission(request, None))
