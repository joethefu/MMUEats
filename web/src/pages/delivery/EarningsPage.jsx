import { useEffect, useState } from "react";
import { deliveryService } from "../../services/deliveryService";

export default function EarningsPage() {
  const [earnings, setEarnings] = useState(null);

  useEffect(() => {
    deliveryService.getEarnings().then(setEarnings);
  }, []);

  if (!earnings) return <p className="text-slate-500">Loading…</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Earnings</h1>
      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Total Earnings</p>
          <p className="mt-1 text-xl font-bold text-slate-900">KES {earnings.total_earnings}</p>
        </div>
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Total Deliveries</p>
          <p className="mt-1 text-xl font-bold text-slate-900">{earnings.total_deliveries}</p>
        </div>
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Today's Earnings</p>
          <p className="mt-1 text-xl font-bold text-slate-900">KES {earnings.today_earnings}</p>
        </div>
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Rating</p>
          <p className="mt-1 text-xl font-bold text-slate-900">{earnings.average_rating || "New"}</p>
        </div>
      </div>
    </div>
  );
}
