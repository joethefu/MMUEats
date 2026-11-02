import { useState, useRef, useEffect } from "react";
import { FaBell } from "react-icons/fa";
import { useNotifications } from "../contexts/NotificationContext";

function timeAgo(dateStr) {
  const seconds = Math.floor((Date.now() - new Date(dateStr)) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function NotificationBell() {
  const { notifications, unreadCount, markRead, markAllRead } = useNotifications();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative flex items-center" ref={ref}>
      <button onClick={() => setOpen((v) => !v)} aria-label="Notifications" className="relative flex h-9 w-9 items-center justify-center text-slate-700 hover:text-brand-600">
        <FaBell size={18} />
        {unreadCount > 0 && (
          <span className="absolute right-0 top-0 flex h-4 w-4 items-center justify-center rounded-full bg-brand-600 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-[min(20rem,calc(100vw-2rem))] rounded-xl border border-slate-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-100 p-3">
            <span className="text-sm font-semibold text-slate-900">Notifications</span>
            {unreadCount > 0 && (
              <button onClick={markAllRead} className="text-xs font-medium text-brand-600 hover:underline">
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 && (
              <p className="p-4 text-center text-sm text-slate-500">No notifications yet.</p>
            )}
            {notifications.map((n) => (
              <button
                key={n.id}
                onClick={() => !n.is_read && markRead(n.id)}
                className={`block w-full border-b border-slate-50 p-3 text-left text-sm hover:bg-slate-50 ${
                  n.is_read ? "" : "bg-brand-50/50"
                }`}
              >
                <p className="font-medium text-slate-900">{n.title}</p>
                <p className="mt-0.5 text-xs text-slate-600">{n.message}</p>
                <p className="mt-1 text-[10px] text-slate-400">{timeAgo(n.created_at)}</p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
