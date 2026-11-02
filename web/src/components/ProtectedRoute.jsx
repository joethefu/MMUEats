import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

/**
 * Guards a route to authenticated users, optionally restricted to specific roles.
 * NOTE: this is a UX convenience only. Every backend endpoint enforces the same
 * (and stricter) checks independently — the frontend guard must never be relied
 * on alone for access control.
 */
export default function ProtectedRoute({ allowedRoles }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center text-slate-500">Loading…</div>;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
