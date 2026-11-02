import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { useCart } from "../contexts/CartContext";
import { orderService } from "../services/orderService";
import { paymentService } from "../services/paymentService";
import { CAMPUS_LOCATIONS } from "../services/userService";

export default function CheckoutPage() {
  const { cart, refreshCart } = useCart();
  const navigate = useNavigate();
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm({
    defaultValues: { payment_method: "cash_on_delivery" },
  });
  const [serverError, setServerError] = useState(null);
  const [mpesaStage, setMpesaStage] = useState(null); // null | "awaiting_phone" (handled by form) | "waiting" | "mocked"
  const [pendingOrderId, setPendingOrderId] = useState(null);
  const [isMocked, setIsMocked] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);

  const paymentMethod = watch("payment_method");

  if (!cart || cart.items.length === 0) {
    return (
      <div className="mx-auto max-w-md px-4 py-24 text-center">
        <p className="text-slate-600">Your cart is empty.</p>
      </div>
    );
  }

  const onSubmit = async (values) => {
    setServerError(null);
    try {
      const order = await orderService.checkout(values);
      await refreshCart();

      if (values.payment_method === "mpesa") {
        setPendingOrderId(order.id);
        setMpesaStage("waiting");
        const stkResult = await paymentService.stkPush({ order_id: order.id, phone_number: values.mpesa_phone });
        setIsMocked(Boolean(stkResult.payment?.is_mocked));
        toast.success(stkResult.message || "Check your phone to complete payment.");
      } else {
        toast.success("Order placed!");
        navigate(`/orders/${order.id}`);
      }
    } catch (err) {
      const message = err?.response?.data?.error?.message || "Checkout failed. Please try again.";
      setServerError(message);
      setMpesaStage(null);
    }
  };

  const handleSimulate = async (success) => {
    setIsSimulating(true);
    try {
      await paymentService.simulate({ order_id: pendingOrderId, success });
      toast.success(success ? "Payment confirmed!" : "Payment marked as failed.");
      navigate(`/orders/${pendingOrderId}`);
    } catch {
      toast.error("Couldn't simulate payment.");
    } finally {
      setIsSimulating(false);
    }
  };

  if (mpesaStage === "waiting") {
    return (
      <div className="mx-auto max-w-md px-4 py-24 text-center">
        <div className="mx-auto h-12 w-12 animate-pulse rounded-full bg-brand-100" />
        <h1 className="mt-4 text-xl font-bold text-slate-900">Check your phone</h1>
        <p className="mt-2 text-sm text-slate-600">
          We've sent an M-Pesa prompt to complete your payment. This page will update once it's confirmed.
        </p>

        {isMocked && (
          <div className="mt-8 rounded-xl border border-dashed border-slate-300 p-4">
            <p className="text-xs text-slate-500">
              Dev mode: M-Pesa credentials aren't configured, so no real prompt was sent. Simulate the outcome below.
            </p>
            <div className="mt-3 flex justify-center gap-3">
              <button
                onClick={() => handleSimulate(true)}
                disabled={isSimulating}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
              >
                Simulate Success
              </button>
              <button
                onClick={() => handleSimulate(false)}
                disabled={isSimulating}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Simulate Failure
              </button>
            </div>
          </div>
        )}

        <button
          onClick={() => navigate(`/orders/${pendingOrderId}`)}
          className="mt-6 text-sm font-medium text-brand-600 hover:underline"
        >
          View order status
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-bold text-slate-900">Checkout</h1>

      <div className="mt-4 rounded-xl border border-slate-200 p-4">
        <p className="text-sm font-medium text-slate-700">Order from {cart.restaurant_name}</p>
        <ul className="mt-2 space-y-1 text-sm text-slate-600">
          {cart.items.map((i) => (
            <li key={i.id} className="flex justify-between gap-3">
              <span className="min-w-0 truncate">{i.quantity} × {i.meal_name}</span>
              <span className="shrink-0">KES {i.line_total}</span>
            </li>
          ))}
        </ul>
        <p className="mt-2 border-t border-slate-100 pt-2 text-sm font-medium text-slate-700">Subtotal: KES {cart.subtotal}</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
        <div>
          <label className="block text-sm font-medium text-slate-700">Delivery Location</label>
          <select
            {...register("delivery_campus_location", { required: "Please select a delivery location" })}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          >
            <option value="">Select a campus location…</option>
            {CAMPUS_LOCATIONS.map((loc) => (
              <option key={loc} value={loc}>{loc}</option>
            ))}
          </select>
          {errors.delivery_campus_location && (
            <p className="mt-1 text-xs text-red-600">{errors.delivery_campus_location.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Additional Directions (optional)</label>
          <input
            {...register("delivery_directions")}
            placeholder="e.g. Room 214, near the stairs"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Payment Method</label>
          <div className="mt-2 space-y-2">
            <label className="flex items-center gap-2 rounded-lg border border-slate-300 p-3 text-sm">
              <input type="radio" value="mpesa" {...register("payment_method")} />
              M-Pesa
            </label>
            <label className="flex items-center gap-2 rounded-lg border border-slate-300 p-3 text-sm">
              <input type="radio" value="cash_on_delivery" {...register("payment_method")} defaultChecked />
              Cash on Delivery
            </label>
          </div>
        </div>

        {paymentMethod === "mpesa" && (
          <div>
            <label className="block text-sm font-medium text-slate-700">M-Pesa Phone Number</label>
            <input
              {...register("mpesa_phone", {
                required: "Phone number is required for M-Pesa",
                pattern: { value: /^254(7|1)\d{8}$/, message: "Format: 2547XXXXXXXX" },
              })}
              placeholder="2547XXXXXXXX"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            />
            {errors.mpesa_phone && <p className="mt-1 text-xs text-red-600">{errors.mpesa_phone.message}</p>}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-slate-700">Coupon Code (optional)</label>
          <input
            {...register("coupon_code")}
            placeholder="e.g. SAVE10"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm uppercase focus:border-brand-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Special Instructions (optional)</label>
          <textarea
            {...register("special_instructions")}
            rows={2}
            placeholder="e.g. Call when you arrive"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          />
        </div>

        {serverError && <p className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{serverError}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {isSubmitting ? "Placing order…" : "Place Order"}
        </button>
      </form>
    </div>
  );
}
