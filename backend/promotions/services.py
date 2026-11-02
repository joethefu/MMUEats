"""Shared coupon-validation logic used by both the standalone /validate/ endpoint and checkout itself."""

from django.utils import timezone

from .models import Coupon, CouponRedemption


class CouponError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


def validate_and_price_coupon(code, customer, restaurant, subtotal, delivery_fee):
    """
    Returns (coupon, discount_amount, free_delivery) if valid, else raises CouponError.
    Does NOT record redemption — that happens at actual checkout time, once the
    order is committed, to avoid burning a use on a validation-only preview call.
    """
    try:
        coupon = Coupon.objects.get(code=code.strip().upper())
    except Coupon.DoesNotExist:
        raise CouponError("invalid_code", "This coupon code doesn't exist.")

    if not coupon.is_currently_valid:
        raise CouponError("expired_or_inactive", "This coupon is no longer valid.")

    if coupon.restaurant_id is not None and coupon.restaurant_id != restaurant.id:
        raise CouponError("wrong_restaurant", "This coupon isn't valid for this restaurant.")

    if subtotal < coupon.min_order_amount:
        raise CouponError(
            "minimum_not_met", f"This coupon requires a minimum order of KES {coupon.min_order_amount}."
        )

    prior_uses = CouponRedemption.objects.filter(coupon=coupon, customer=customer).count()
    if prior_uses >= coupon.max_uses_per_customer:
        raise CouponError("already_used", "You've already used this coupon the maximum number of times.")

    discount_amount, free_delivery = coupon.compute_discount(subtotal, delivery_fee)
    return coupon, discount_amount, free_delivery


def redeem_coupon(coupon, customer, order):
    CouponRedemption.objects.create(coupon=coupon, customer=customer, order=order)
    coupon.used_count += 1
    coupon.save(update_fields=["used_count"])
