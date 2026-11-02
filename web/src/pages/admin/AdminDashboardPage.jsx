import { useEffect, useState } from "react";
import { adminService } from "../../services/adminService";

const STAT_CARDS = [
  { key: "total_users", label: "Total Customers" },
  { key: "total_vendors", label: "Total Vendors" },
  { key: "total_delivery_partners", label: "Total Delivery Partners" },
  { key: "total_orders", label: "Total Orders" },
  { key: "pending_orders", label: "Pending Orders" },
  { key: "completed_orders", label: "Completed Orders" },
  { key: "cancelled_orders", label: "Cancelled Orders" },
  { key: "total_revenue", label: "Total Revenue", prefix: "KES " },
];

export default function AdminDashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    adminService.getDashboard().then(setDashboard).finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <p className="text-slate-500">Loading dashboard…</p>;
  if (!dashboard) return <p className="text-slate-500">Couldn't load dashboard.</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Platform Overview</h1>

      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {STAT_CARDS.map((c) => (
          <div key={c.key} className="rounded-xl border border-slate-200 p-4">
            <p className="text-xs text-slate-500">{c.label}</p>
            <p className="mt-1 text-xl font-bold text-slate-900">{c.prefix || ""}{dashboard[c.key]}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Today's Revenue</p>
          <p className="mt-1 text-lg font-bold text-slate-900">KES {dashboard.daily_revenue}</p>
        </div>
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">This Week</p>
          <p className="mt-1 text-lg font-bold text-slate-900">KES {dashboard.weekly_revenue}</p>
        </div>
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">This Month</p>
          <p className="mt-1 text-lg font-bold text-slate-900">KES {dashboard.monthly_revenue}</p>
        </div>
      </div>

      {(dashboard.pending_vendor_applications > 0 || dashboard.pending_delivery_applications > 0) && (
        <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          {dashboard.pending_vendor_applications > 0 && <p>{dashboard.pending_vendor_applications} vendor application(s) awaiting review.</p>}
          {dashboard.pending_delivery_applications > 0 && <p>{dashboard.pending_delivery_applications} delivery partner application(s) awaiting review.</p>}
        </div>
      )}

      <div className="mt-8 grid gap-6 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 p-4">
          <h2 className="font-semibold text-slate-900">Popular Meals</h2>
          {dashboard.popular_meals.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">No sales yet.</p>
          ) : (
            <ol className="mt-3 space-y-2">
              {dashboard.popular_meals.map((m, i) => (
                <li key={m.id} className="flex justify-between text-sm">
                  <span>{i + 1}. {m.name}</span>
                  <span className="text-slate-500">{m.order_count} sold</span>
                </li>
              ))}
            </ol>
          )}
        </div>
        <div className="rounded-xl border border-slate-200 p-4">
          <h2 className="font-semibold text-slate-900">Popular Restaurants</h2>
          {dashboard.popular_restaurants.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">No ratings yet.</p>
          ) : (
            <ol className="mt-3 space-y-2">
              {dashboard.popular_restaurants.map((r, i) => (
                <li key={r.id} className="flex justify-between text-sm">
                  <span>{i + 1}. {r.name}</span>
                  <span className="text-slate-500">{r.average_rating}★ ({r.ratings_count})</span>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </div>
  );
}
