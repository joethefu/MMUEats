import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { deliveryService } from "../../services/deliveryService";

export default function DeliveryDashboardPage() {
  const [profile, setProfile] = useState(null);
  const [earnings, setEarnings] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const load = () => Promise.all([deliveryService.getProfile(), deliveryService.getEarnings()]).then(([p, e]) => {
    setProfile(p);
    setEarnings(e);
  });

  useEffect(() => {
    load().finally(() => setIsLoading(false));
  }, []);

  const toggleOnline = async () => {
    try {
      const updated = await deliveryService.updateProfile({ is_online: !profile.is_online });
      setProfile(updated);
      toast.success(updated.is_online ? "You're online" : "You're offline");
    } catch {
      toast.error("Couldn't update your status.");
    }
  };

  if (isLoading || !profile) return <p className="text-slate-500">Loading…</p>;

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Welcome, {profile.full_name?.split(" ")[0]}</h1>
        <button
          onClick={toggleOnline}
          className={`rounded-full px-5 py-2 text-sm font-semibold ${
            profile.is_online ? "bg-green-600 text-white" : "bg-slate-200 text-slate-700"
          }`}
        >
          {profile.is_online ? "Online" : "Offline"}
        </button>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Today's Deliveries</p>
          <p className="mt-1 text-xl font-bold text-slate-900">{earnings.today_deliveries}</p>
        </div>
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Today's Earnings</p>
          <p className="mt-1 text-xl font-bold text-slate-900">KES {earnings.today_earnings}</p>
        </div>
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Total Deliveries</p>
          <p className="mt-1 text-xl font-bold text-slate-900">{earnings.total_deliveries}</p>
        </div>
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Rating</p>
          <p className="mt-1 text-xl font-bold text-slate-900">{earnings.average_rating || "New"}</p>
        </div>
      </div>

      {!profile.is_online && (
        <p className="mt-6 rounded-lg bg-amber-50 border border-amber-200 p-3 text-sm text-amber-800">
          You're offline — go online to see available deliveries.
        </p>
      )}
    </div>
  );
}
