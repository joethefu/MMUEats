import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { vendorService } from "../../services/vendorService";

const NEXT_ACTIONS = {
  pending: [{ status: "accepted", label: "Accept" }, { status: "rejected", label: "Reject" }],
  accepted: [{ status: "preparing", label: "Start Preparing" }],
  preparing: [{ status: "ready_for_pickup", label: "Mark Ready for Pickup" }],
  ready_for_pickup: [],
  picked_up: [],
  out_for_delivery: [],
};

export default function VendorOrdersPage() {
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState("");

  const load = () => vendorService.listOrders(filter ? { status: filter } : {}).then((data) => setOrders(data.results || []));

  useEffect(() => {
    setIsLoading(true);
    load().finally(() => setIsLoading(false));
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const handleAction = async (order, status) => {
    try {
      await vendorService.updateOrderStatus(order.id, { status });
      toast.success(`Order marked as ${status.replace(/_/g, " ")}`);
      load();
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || "Couldn't update this order.");
    }
  };

  if (isLoading) return <p className="text-slate-500">Loading orders…</p>;

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Orders</h1>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm">
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="accepted">Accepted</option>
          <option value="preparing">Preparing</option>
          <option value="ready_for_pickup">Ready for Pickup</option>
          <option value="delivered">Delivered</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {orders.length === 0 && <p className="mt-6 text-sm text-slate-500">No orders here yet.</p>}

      <div className="mt-6 space-y-4">
        {orders.map((order) => (
          <div key={order.id} className="rounded-xl border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-slate-900">#{order.order_number} — {order.customer_name}</p>
                <p className="text-xs text-slate-500">{order.customer_phone} · Deliver to: {order.delivery_campus_location}</p>
              </div>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium capitalize text-slate-700">
                {order.status.replace(/_/g, " ")}
              </span>
            </div>

            <ul className="mt-3 space-y-1 text-sm text-slate-600">
              {order.items.map((item) => (
                <li key={item.id}>
                  {item.quantity}x {item.meal_name}
                  {item.special_instructions && <span className="text-slate-400"> — {item.special_instructions}</span>}
                </li>
              ))}
            </ul>

            <p className="mt-2 text-sm font-medium text-slate-900">Total: KES {order.total}</p>

            {order.special_instructions && (
              <p className="mt-1 text-xs text-slate-500">Note: {order.special_instructions}</p>
            )}

            <div className="mt-3 flex gap-2">
              {(NEXT_ACTIONS[order.status] || []).map((action) => (
                <button
                  key={action.status}
                  onClick={() => handleAction(order, action.status)}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                    action.status === "rejected"
                      ? "border border-red-300 text-red-600 hover:bg-red-50"
                      : "bg-brand-600 text-white hover:bg-brand-700"
                  }`}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
