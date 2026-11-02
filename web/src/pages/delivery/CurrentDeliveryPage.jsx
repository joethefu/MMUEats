import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { deliveryService } from "../../services/deliveryService";

const NEXT_ACTION = {
  ready_for_pickup: { status: "picked_up", label: "Confirm Pickup" },
  picked_up: { status: "out_for_delivery", label: "Start Delivery" },
  out_for_delivery: { status: "delivered", label: "Confirm Delivered" },
};

export default function CurrentDeliveryPage() {
  const [deliveries, setDeliveries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const load = () =>
    deliveryService.listMine().then((data) => {
      const active = (data.results || data).filter((d) => !d.delivered_at);
      setDeliveries(active);
    });

  useEffect(() => {
    load().finally(() => setIsLoading(false));
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAdvance = async (delivery) => {
    const next = NEXT_ACTION[delivery.order_status];
    if (!next) return;
    try {
      await deliveryService.updateOrderStatus(delivery.order, { status: next.status });
      toast.success(`Marked as ${next.status.replace(/_/g, " ")}`);
      load();
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || "Couldn't update this delivery.");
    }
  };

  const handleReject = async (delivery) => {
    try {
      await deliveryService.reject(delivery.id);
      toast.success("Delivery released.");
      load();
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || "Couldn't reject this delivery.");
    }
  };

  if (isLoading) return <p className="text-slate-500">Loading…</p>;

  if (deliveries.length === 0) {
    return <p className="text-sm text-slate-500">No active delivery. Check Available Orders to pick one up.</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Current Delivery</h1>
      <div className="mt-6 space-y-4">
        {deliveries.map((d) => {
          const next = NEXT_ACTION[d.order_status];
          return (
            <div key={d.id} className="rounded-xl border border-slate-200 p-4">
              <p className="font-medium text-slate-900">#{d.order_number} — {d.restaurant_name}</p>
              <p className="text-sm text-slate-500">
                Pickup: {d.restaurant_location} → Deliver to: {d.delivery_campus_location}
                {d.delivery_directions && ` (${d.delivery_directions})`}
              </p>
              <p className="mt-1 text-sm text-slate-600">Customer: {d.customer_name} · {d.customer_phone}</p>
              <p className="mt-1 text-sm font-medium text-slate-900">KES {d.order_total}</p>
              <span className="mt-2 inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium capitalize text-slate-700">
                {d.order_status.replace(/_/g, " ")}
              </span>

              <div className="mt-4 flex gap-2">
                {next && (
                  <button onClick={() => handleAdvance(d)} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
                    {next.label}
                  </button>
                )}
                {!d.picked_up_at && (
                  <button onClick={() => handleReject(d)} className="rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50">
                    Reject
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
