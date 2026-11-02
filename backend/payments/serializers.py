from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "order", "order_number", "method", "status", "amount",
            "phone_number", "mpesa_receipt_number", "transaction_date",
            "is_mocked", "created_at",
        ]
        read_only_fields = fields


class STKPushRequestSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    phone_number = serializers.RegexField(
        regex=r"^2547\d{8}$|^2541\d{8}$",
        error_messages={"invalid": "Enter a valid Safaricom number in the format 2547XXXXXXXX."},
    )
