import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { adminService } from "../../services/adminService";

const ROLES = [
  { value: "", label: "All roles" },
  { value: "customer", label: "Customers" },
  { value: "vendor", label: "Vendors" },
  { value: "delivery_partner", label: "Delivery Partners" },
  { value: "admin", label: "Admins" },
];

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [role, setRole] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = () => adminService.listUsers(role ? { role } : {}).then((data) => setUsers(data.results || []));

  useEffect(() => {
    setIsLoading(true);
    load().finally(() => setIsLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role]);

  const handleToggleSuspend = async (user) => {
    try {
      if (user.is_suspended) {
        await adminService.reactivateUser(user.id);
        toast.success(`${user.email} reactivated`);
      } else {
        await adminService.suspendUser(user.id);
        toast.success(`${user.email} suspended`);
      }
      load();
    } catch {
      toast.error("Couldn't update this user.");
    }
  };

  if (isLoading) return <p className="text-slate-500">Loading…</p>;

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Users</h1>
        <select value={role} onChange={(e) => setRole(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm">
          {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
        </select>
      </div>

      <div className="mt-6 divide-y divide-slate-200 rounded-xl border border-slate-200">
        {users.length === 0 && <p className="p-4 text-sm text-slate-500">No users found.</p>}
        {users.map((u) => (
          <div key={u.id} className="flex items-center justify-between gap-4 p-4">
            <div>
              <p className="font-medium text-slate-900">{u.full_name} <span className="text-xs text-slate-400">({u.role})</span></p>
              <p className="text-sm text-slate-500">{u.email} · {u.phone_number || "no phone"}</p>
              <div className="mt-1 flex gap-2 text-xs">
                {u.is_email_verified ? <span className="text-green-600">Verified</span> : <span className="text-amber-600">Unverified</span>}
                {u.is_suspended && <span className="font-medium text-red-600">Suspended</span>}
              </div>
            </div>
            <button
              onClick={() => handleToggleSuspend(u)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                u.is_suspended ? "bg-brand-600 text-white hover:bg-brand-700" : "border border-red-300 text-red-600 hover:bg-red-50"
              }`}
            >
              {u.is_suspended ? "Reactivate" : "Suspend"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
