import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { vendorService } from "../../services/vendorService";

const STAT_CARDS = [
  { key: "today_orders_count", label: "Today's Orders" },
  { key: "today_revenue", label: "Today's Revenue", prefix: "KES " },
  { key: "pending_orders_count", label: "Pending Orders" },
  { key: "completed_orders_count", label: "Completed Orders" },
  { key: "cancelled_orders_count", label: "Cancelled Orders" },
];

export default function VendorDashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [notSetUp, setNotSetUp] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    vendorService
      .getDashboard()
      .then(setDashboard)
      .catch((err) => {
        if (err?.response?.status === 404) setNotSetUp(true);
      })
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <p className="text-slate-500">Loading dashboard…</p>;

  if (notSetUp) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center">
        <h2 className="text-lg font-semibold text-slate-900">Set up your restaurant first</h2>
        <p className="mt-2 text-sm text-slate-600">You need a restaurant profile before you can receive orders.</p>
        <Link to="/vendor/restaurant" className="mt-4 inline-block rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-700">
          Create Restaurant Profile
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">{dashboard.restaurant_name}</h1>
      <p className="mt-1 text-sm text-slate-500 capitalize">Status: {dashboard.restaurant_status}</p>

      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {STAT_CARDS.map((c) => (
          <div key={c.key} className="rounded-xl border border-slate-200 p-4">
            <p className="text-xs text-slate-500">{c.label}</p>
            <p className="mt-1 text-xl font-bold text-slate-900">{c.prefix || ""}{dashboard[c.key]}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 rounded-xl border border-slate-200 p-4">
        <h2 className="font-semibold text-slate-900">Most Sold Meals</h2>
        {dashboard.most_sold_meals.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">No sales yet.</p>
        ) : (
          <ol className="mt-3 space-y-2">
            {dashboard.most_sold_meals.map((m, i) => (
              <li key={m.id} className="flex justify-between text-sm">
                <span>{i + 1}. {m.name}</span>
                <span className="text-slate-500">{m.order_count} sold</span>
              </li>
            ))}
          </ol>
        )}
      </div>

      <div className="mt-6 flex items-center gap-2 text-sm text-slate-600">
        <span>Rating:</span>
        <span className="font-semibold text-slate-900">{dashboard.average_rating || "New"}</span>
        <span>({dashboard.ratings_count} reviews)</span>
      </div>
    </div>
  );
}
