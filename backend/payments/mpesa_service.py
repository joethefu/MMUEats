"""
M-Pesa Daraja API integration (STK Push / Lipa Na M-Pesa Online).

DEVELOPMENT MODE: when MPESA_CONSUMER_KEY is not set in the environment, every
function here returns a realistic mocked response instead of calling Safaricom,
so checkout, payment history, and the webhook flow can all be built and tested
without waiting on sandbox credentials. Set MPESA_CONSUMER_KEY/SECRET/PASSKEY/
SHORTCODE in .env to switch to the real Safaricom sandbox — no other code needs
to change.
"""

import base64
import logging
import uuid
from datetime import datetime

import requests
from django.conf import settings

logger = logging.getLogger("django")

SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"
PRODUCTION_BASE_URL = "https://api.safaricom.co.ke"


def _is_configured():
    return bool(settings.MPESA_CONSUMER_KEY and settings.MPESA_CONSUMER_SECRET and settings.MPESA_PASSKEY)


def _base_url():
    return PRODUCTION_BASE_URL if settings.MPESA_ENV == "production" else SANDBOX_BASE_URL


def get_access_token():
    """OAuth token from Safaricom. Returns a fake token in mock mode."""
    if not _is_configured():
        return "mock-access-token"

    url = f"{_base_url()}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET), timeout=15)
    response.raise_for_status()
    return response.json()["access_token"]


def _generate_password(timestamp):
    raw = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


def stk_push(*, phone_number, amount, account_reference, transaction_desc):
    """
    Initiates an STK push prompt on the customer's phone.
    Returns a dict shaped like Safaricom's real response:
    {merchant_request_id, checkout_request_id, response_code, response_description, is_mocked}
    """
    if not _is_configured():
        logger.warning(
            "M-Pesa credentials not configured — returning a MOCKED STK push response for order %s. "
            "Set MPESA_CONSUMER_KEY/SECRET/PASSKEY in .env for real Safaricom sandbox calls.",
            account_reference,
        )
        return {
            "merchant_request_id": f"mock-merchant-{uuid.uuid4().hex[:12]}",
            "checkout_request_id": f"mock-checkout-{uuid.uuid4().hex[:12]}",
            "response_code": "0",
            "response_description": "Success. Request accepted for processing (MOCKED — no real STK push sent).",
            "is_mocked": True,
        }

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": _generate_password(timestamp),
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc,
    }
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    url = f"{_base_url()}/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    return {
        "merchant_request_id": data.get("MerchantRequestID", ""),
        "checkout_request_id": data.get("CheckoutRequestID", ""),
        "response_code": data.get("ResponseCode", ""),
        "response_description": data.get("ResponseDescription", ""),
        "is_mocked": False,
    }


def simulate_mock_callback_payload(checkout_request_id, merchant_request_id, amount, phone_number, success=True):
    """
    Builds a Safaricom-shaped callback payload for mock-mode "instant success" testing —
    used by the dev-only /api/payments/mpesa/simulate/ endpoint (never exposed in production,
    since real Safaricom sends this to MPESA_CALLBACK_URL on its own).
    """
    if success:
        receipt = f"MOCK{uuid.uuid4().hex[:8].upper()}"
        return {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": merchant_request_id,
                    "CheckoutRequestID": checkout_request_id,
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": float(amount)},
                            {"Name": "MpesaReceiptNumber", "Value": receipt},
                            {"Name": "TransactionDate", "Value": int(datetime.now().strftime("%Y%m%d%H%M%S"))},
                            {"Name": "PhoneNumber", "Value": phone_number},
                        ]
                    },
                }
            }
        }
    return {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": merchant_request_id,
                "CheckoutRequestID": checkout_request_id,
                "ResultCode": 1032,
                "ResultDesc": "Request cancelled by user.",
            }
        }
    }
