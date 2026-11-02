import uuid

from django.db import models

from common.models import TimeStampedModel
from orders.models import Order


class Payment(TimeStampedModel):
    """
    One per Order. Created at checkout time for BOTH payment methods so payment
    history is uniform — Cash on Delivery starts 'pending' and is marked 'paid'
    on delivery; M-Pesa starts 'pending' and moves through 'processing' once an
    STK push is initiated, then 'paid'/'failed' once Safaricom's callback lands.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=20, choices=Order.PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # M-Pesa Daraja fields — populated once an STK push is initiated / confirmed.
    phone_number = models.CharField(max_length=20, blank=True)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, db_index=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    result_code = models.IntegerField(null=True, blank=True)
    result_desc = models.CharField(max_length=255, blank=True)
    raw_callback = models.JSONField(default=dict, blank=True)  # full Safaricom payload, for audit/debugging
    is_mocked = models.BooleanField(default=False)  # True when MPESA_CONSUMER_KEY isn't configured

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"Payment({self.order.order_number}, {self.method}, {self.status})"
