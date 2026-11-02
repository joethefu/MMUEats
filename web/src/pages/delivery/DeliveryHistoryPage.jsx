import { useEffect, useState } from "react";
import { deliveryService } from "../../services/deliveryService";

export default function DeliveryHistoryPage() {
  const [deliveries, setDeliveries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    deliveryService
      .listMine()
      .then((data) => setDeliveries((data.results || data).filter((d) => d.delivered_at)))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <p className="text-slate-500">Loading…</p>;

  if (deliveries.length === 0) return <p className="text-sm text-slate-500">No completed deliveries yet.</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Delivery History</h1>
      <div className="mt-6 divide-y divide-slate-200 rounded-xl border border-slate-200">
        {deliveries.map((d) => (
          <div key={d.id} className="flex items-center justify-between p-4 text-sm">
            <div>
              <p className="font-medium text-slate-900">#{d.order_number} — {d.restaurant_name}</p>
              <p className="text-slate-500">{new Date(d.delivered_at).toLocaleString()}</p>
            </div>
            <span className="font-medium text-slate-900">+KES {d.earnings}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
