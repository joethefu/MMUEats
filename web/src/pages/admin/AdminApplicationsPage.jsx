import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { adminService } from "../../services/adminService";

export default function AdminApplicationsPage() {
  const [vendorApps, setVendorApps] = useState([]);
  const [deliveryApps, setDeliveryApps] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const load = () =>
    Promise.all([
      adminService.listVendorApplications({ status: "pending" }),
      adminService.listDeliveryApplications({ status: "pending" }),
    ]).then(([v, d]) => {
      setVendorApps(v.results || []);
      setDeliveryApps(d.results || []);
    });

  useEffect(() => {
    load().finally(() => setIsLoading(false));
  }, []);

  const reviewVendor = async (id, action) => {
    try {
      await adminService.reviewVendorApplication(id, { action });
      toast.success(`Application ${action}d`);
      load();
    } catch {
      toast.error("Couldn't process this application.");
    }
  };

  const reviewDelivery = async (id, action) => {
    try {
      await adminService.reviewDeliveryApplication(id, { action });
      toast.success(`Application ${action}d`);
      load();
    } catch {
      toast.error("Couldn't process this application.");
    }
  };

  if (isLoading) return <p className="text-slate-500">Loading…</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Pending Applications</h1>

      <h2 className="mt-8 font-semibold text-slate-900">Vendor Applications</h2>
      {vendorApps.length === 0 && <p className="mt-2 text-sm text-slate-500">No pending vendor applications.</p>}
      <div className="mt-3 space-y-3">
        {vendorApps.map((app) => (
          <div key={app.id} className="rounded-xl border border-slate-200 p-4">
            <p className="font-medium text-slate-900">{app.business_name}</p>
            <p className="text-sm text-slate-500">{app.owner_name} · {app.email} · {app.phone_number}</p>
            <p className="text-sm text-slate-500">{app.business_location}</p>
            <div className="mt-3 flex gap-2">
              <button onClick={() => reviewVendor(app.id, "approve")} className="rounded-lg bg-brand-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-brand-700">
                Approve
              </button>
              <button onClick={() => reviewVendor(app.id, "reject")} className="rounded-lg border border-red-300 px-4 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50">
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>

      <h2 className="mt-10 font-semibold text-slate-900">Delivery Partner Applications</h2>
      {deliveryApps.length === 0 && <p className="mt-2 text-sm text-slate-500">No pending delivery partner applications.</p>}
      <div className="mt-3 space-y-3">
        {deliveryApps.map((app) => (
          <div key={app.id} className="rounded-xl border border-slate-200 p-4">
            <p className="font-medium text-slate-900">{app.full_name}</p>
            <p className="text-sm text-slate-500">{app.email} · {app.phone_number}</p>
            <p className="text-sm text-slate-500">Preferred area: {app.preferred_area}</p>
            <div className="mt-3 flex gap-2">
              <button onClick={() => reviewDelivery(app.id, "approve")} className="rounded-lg bg-brand-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-brand-700">
                Approve
              </button>
              <button onClick={() => reviewDelivery(app.id, "reject")} className="rounded-lg border border-red-300 px-4 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50">
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
