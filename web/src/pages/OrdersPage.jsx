import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { orderService } from "../services/orderService";

const STATUS_COLORS = {
  pending: "bg-amber-100 text-amber-700",
  accepted: "bg-blue-100 text-blue-700",
  preparing: "bg-blue-100 text-blue-700",
  ready_for_pickup: "bg-indigo-100 text-indigo-700",
  picked_up: "bg-indigo-100 text-indigo-700",
  out_for_delivery: "bg-purple-100 text-purple-700",
  delivered: "bg-green-100 text-green-700",
  cancelled: "bg-slate-100 text-slate-500",
  rejected: "bg-red-100 text-red-700",
};

export default function OrdersPage() {
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    orderService.list().then((data) => setOrders(data.results || [])).finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <div className="mx-auto max-w-3xl px-4 py-16 text-slate-500">Loading orders…</div>;

  if (orders.length === 0) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center px-4 py-24 text-center">
        <h1 className="text-2xl font-bold text-slate-900">No orders yet</h1>
        <Link to="/restaurants" className="mt-6 rounded-lg bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
          Order something
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-bold text-slate-900">Your Orders</h1>
      <div className="mt-6 space-y-4">
        {orders.map((order) => (
          <Link
            key={order.id}
            to={`/orders/${order.id}`}
            className="block rounded-xl border border-slate-200 p-4 hover:shadow-sm"
          >
            <div className="flex items-center justify-between">
              <p className="font-medium text-slate-900">{order.restaurant_name}</p>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[order.status]}`}>
                {order.status.replace(/_/g, " ")}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-500">#{order.order_number} · KES {order.total}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
