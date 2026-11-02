import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { orderService } from "../services/orderService";
import { paymentService } from "../services/paymentService";
import { useCart } from "../contexts/CartContext";
import { getWebSocketUrl } from "../services/notificationService";
import { tokenStorage } from "../services/apiClient";

const STATUS_STEPS = ["pending", "accepted", "preparing", "ready_for_pickup", "picked_up", "out_for_delivery", "delivered"];

export default function OrderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { refreshCart } = useCart();
  const [order, setOrder] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const load = () => orderService.get(id).then(setOrder).finally(() => setIsLoading(false));

  useEffect(() => {
    load();
    // Live updates via WebSocket, with polling as a fallback in case the socket
    // can't connect (network issues, no WS support) — belt and suspenders.
    const token = tokenStorage.getAccess();
    let ws;
    if (token) {
      ws = new WebSocket(getWebSocketUrl(`/ws/notifications/?token=${token}`));
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event === "order_update" && payload.order_id === id) {
            load();
          }
        } catch {
          // ignore malformed frames
        }
      };
    }
    const interval = setInterval(load, 20000);
    return () => {
      clearInterval(interval);
      ws?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleCancel = async () => {
    try {
      const updated = await orderService.cancel(id);
      setOrder(updated);
      toast.success("Order cancelled.");
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || "Couldn't cancel this order.");
    }
  };

  const handleReorder = async () => {
    try {
      await orderService.reorder(id);
      await refreshCart();
      toast.success("Added to cart!");
      navigate("/cart");
    } catch {
      toast.error("Couldn't reorder right now.");
    }
  };

  const [isRetrying, setIsRetrying] = useState(false);
  const handleRetryPayment = async () => {
    const phone = prompt("Enter your M-Pesa phone number (format 2547XXXXXXXX):");
    if (!phone) return;
    setIsRetrying(true);
    try {
      const result = await paymentService.stkPush({ order_id: id, phone_number: phone });
      toast.success(result.message || "Check your phone to complete payment.");
      if (result.payment?.is_mocked) {
        toast((t) => (
          <span>
            Dev mode — simulate it?{" "}
            <button
              className="ml-2 font-semibold underline"
              onClick={async () => {
                await paymentService.simulate({ order_id: id, success: true });
                toast.dismiss(t.id);
                load();
              }}
            >
              Simulate Success
            </button>
          </span>
        ), { duration: 8000 });
      }
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || "Couldn't start M-Pesa payment.");
    } finally {
      setIsRetrying(false);
    }
  };

  if (isLoading || !order) return <div className="mx-auto max-w-2xl px-4 py-16 text-slate-500">Loading order…</div>;

  const isTerminal = ["cancelled", "rejected"].includes(order.status);
  const currentStepIndex = STATUS_STEPS.indexOf(order.status);

  return (
    <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-bold text-slate-900">Order #{order.order_number}</h1>
      <p className="mt-1 text-sm text-slate-500">{order.restaurant_name} · KES {order.total}</p>

      {!isTerminal ? (
        <div className="mt-8 flex items-center justify-between">
          {STATUS_STEPS.map((step, i) => (
            <div key={step} className="flex flex-1 flex-col items-center text-center">
              <div
                className={`h-3 w-3 rounded-full ${i <= currentStepIndex ? "bg-brand-600" : "bg-slate-200"}`}
              />
              <span className="mt-1 text-[10px] capitalize text-slate-500">{step.replace(/_/g, " ")}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-6 rounded-lg bg-slate-100 p-3 text-sm text-slate-600 capitalize">
          Order {order.status}{order.cancellation_reason ? `: ${order.cancellation_reason}` : ""}
        </p>
      )}

      <div className="mt-8 rounded-xl border border-slate-200 divide-y divide-slate-200">
        {order.items.map((item) => (
          <div key={item.id} className="flex justify-between p-4 text-sm">
            <span>
              {item.quantity}x {item.meal_name}
              {Number(item.packaging_fee) > 0 && (
                <span className="block text-xs text-slate-500">incl. container KES {item.packaging_fee} each</span>
              )}
            </span>
            <span>KES {item.line_total}</span>
          </div>
        ))}
      </div>

      <div className="mt-4 space-y-1 text-sm text-slate-600">
        <p>Delivering to: {order.delivery_campus_location} {order.delivery_directions && `(${order.delivery_directions})`}</p>
        <p>Payment: {order.payment_method.replace(/_/g, " ")} · <span className="font-medium">{order.payment_status}</span></p>
      </div>

      {order.payment_method === "mpesa" && order.payment_status === "pending" && !isTerminal && (
        <button
          onClick={handleRetryPayment}
          disabled={isRetrying}
          className="mt-3 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {isRetrying ? "Starting…" : "Pay with M-Pesa"}
        </button>
      )}

      <div className="mt-8 flex gap-3">
        {order.can_be_cancelled_by_customer && (
          <button onClick={handleCancel} className="rounded-lg border border-red-300 px-4 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50">
            Cancel Order
          </button>
        )}
        {order.status === "delivered" && (
          <button onClick={handleReorder} className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
            Reorder
          </button>
        )}
      </div>
    </div>
  );
}
