import { useEffect } from "react";
import { FaSignOutAlt } from "react-icons/fa";

export default function LogoutConfirmModal({ open, onCancel, onConfirm, isLoading }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && !isLoading && onCancel();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onCancel, isLoading]);

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 px-4"
      onMouseDown={(e) => e.target === e.currentTarget && !isLoading && onCancel()}
    >
      <div role="dialog" aria-modal="true" aria-labelledby="logout-title" className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600">
          <FaSignOutAlt />
        </div>
        <h2 id="logout-title" className="mt-4 text-center text-lg font-semibold text-slate-900">Log out?</h2>
        <p className="mt-1 text-center text-sm text-slate-500">Are you sure you want to log out of MMUEats?</p>
        <div className="mt-6 flex gap-3">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1 rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60"
          >
            {isLoading ? "Logging out…" : "Log out"}
          </button>
        </div>
      </div>
    </div>
  );
}
