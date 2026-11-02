import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { deliveryService } from "../../services/deliveryService";

export default function AvailableDeliveriesPage() {
  const [deliveries, setDeliveries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const load = () => deliveryService.listAvailable().then(setDeliveries);

  useEffect(() => {
    load().finally(() => setIsLoading(false));
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAccept = async (delivery) => {
    try {
      await deliveryService.accept(delivery.id);
      toast.success("Delivery accepted!");
      navigate("/delivery/current");
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || "Someone else may have already taken this delivery.");
      load();
    }
  };

  if (isLoading) return <p className="text-slate-500">Loading…</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Available Deliveries</h1>

      {deliveries.length === 0 && <p className="mt-6 text-sm text-slate-500">No deliveries available right now. Check back soon!</p>}

      <div className="mt-6 space-y-4">
        {deliveries.map((d) => (
          <div key={d.id} className="rounded-xl border border-slate-200 p-4">
            <p className="font-medium text-slate-900">{d.restaurant_name}</p>
            <p className="text-sm text-slate-500">{d.restaurant_location} → {d.delivery_campus_location}</p>
            <p className="mt-1 text-sm text-slate-600">Order total: KES {d.order_total}</p>
            <button
              onClick={() => handleAccept(d)}
              className="mt-3 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
            >
              Accept Delivery
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
