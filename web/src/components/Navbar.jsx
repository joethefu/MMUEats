import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { FaBars, FaTimes, FaShoppingCart, FaStore, FaThLarge, FaUser } from "react-icons/fa";
import { useAuth } from "../contexts/AuthContext";
import { useCart } from "../contexts/CartContext";
import NotificationBell from "./NotificationBell";
import Avatar from "./Avatar";
import SearchBar from "./SearchBar";

const DASHBOARD_BY_ROLE = {
  customer: "/dashboard",
  vendor: "/vendor/dashboard",
  delivery_partner: "/delivery/dashboard",
  admin: "/admin/dashboard",
};

const desktopLink = ({ isActive }) =>
  `text-sm font-medium hover:text-brand-600 ${isActive ? "text-brand-600" : "text-slate-700"}`;

export default function Navbar() {
  const { user } = useAuth();
  const { itemCount } = useCart();
  const [open, setOpen] = useState(false);
  const dashboardPath = user ? DASHBOARD_BY_ROLE[user.role] || "/dashboard" : null;

  const cartIcon = user?.role === "customer" && (
    <Link to="/cart" aria-label="Cart" className="relative flex h-9 w-9 items-center justify-center text-slate-700 hover:text-brand-600">
      <FaShoppingCart size={18} />
      {itemCount > 0 && (
        <span className="absolute right-0 top-0 flex h-4 w-4 items-center justify-center rounded-full bg-brand-600 text-[10px] font-bold text-white">
          {itemCount}
        </span>
      )}
    </Link>
  );

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <Link to="/" className="text-xl font-bold tracking-tight text-brand-600">
            MMU<span className="text-gold-500">Eats</span>
          </Link>

          {/* Search (desktop) */}
          <SearchBar className="mx-6 hidden max-w-md flex-1 md:block" />

          {/* Desktop */}
          <div className="hidden items-center gap-6 md:flex">
            <NavLink to="/restaurants" className={desktopLink}>Vendors</NavLink>
            {user ? (
              <>
                <NavLink to={dashboardPath} end className={desktopLink}>Dashboard</NavLink>
                <div className="flex items-center gap-1">
                  <NotificationBell />
                  {cartIcon}
                  <Link to="/profile" aria-label="Profile" className="ml-3 rounded-full ring-2 ring-transparent hover:ring-brand-200">
                    <Avatar user={user} size={32} />
                  </Link>
                </div>
              </>
            ) : (
              <>
                <Link to="/about" className="text-sm font-medium text-slate-700 hover:text-brand-600">About</Link>
                <Link to="/help" className="text-sm font-medium text-slate-700 hover:text-brand-600">Help</Link>
                <div className="flex items-center gap-3">
                  <Link to="/login" className="text-sm font-medium text-slate-700 hover:text-brand-600">Log in</Link>
                  <Link to="/signup" className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
                    Sign Up
                  </Link>
                </div>
              </>
            )}
          </div>

          {/* Mobile top bar */}
          {user ? (
            <div className="flex items-center gap-1 md:hidden">
              <NotificationBell />
              {cartIcon}
            </div>
          ) : (
            <button className="md:hidden" onClick={() => setOpen((v) => !v)} aria-label="Toggle menu">
              {open ? <FaTimes size={20} /> : <FaBars size={20} />}
            </button>
          )}
        </nav>

        {/* Search (mobile): its own row under the top bar */}
        <div className="px-4 pb-3 md:hidden">
          <SearchBar />
        </div>

        {!user && open && (
          <div className="border-t border-slate-200 bg-white px-4 py-4 md:hidden">
            <div className="flex flex-col gap-3">
              <Link to="/restaurants" onClick={() => setOpen(false)} className="text-sm font-medium text-slate-700">Vendors</Link>
              <Link to="/about" onClick={() => setOpen(false)} className="text-sm font-medium text-slate-700">About</Link>
              <Link to="/help" onClick={() => setOpen(false)} className="text-sm font-medium text-slate-700">Help</Link>
              <Link to="/login" onClick={() => setOpen(false)} className="text-sm font-medium text-slate-700">Log in</Link>
              <Link to="/signup" onClick={() => setOpen(false)} className="text-sm font-semibold text-brand-600">Sign Up</Link>
            </div>
          </div>
        )}
      </header>

      {/* Mobile primary navigation (signed in): Vendors · Dashboard · Profile */}
      {user && (
        <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white md:hidden" aria-label="Primary">
          <div className="grid grid-cols-3 pb-[env(safe-area-inset-bottom)]">
            {[
              { to: "/restaurants", label: "Vendors", Icon: FaStore, end: false },
              { to: dashboardPath, label: "Dashboard", Icon: FaThLarge, end: true },
              { to: "/profile", label: "Profile", Icon: FaUser, end: false },
            ].map(({ to, label, Icon, end }) => (
              <NavLink
                key={label}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium ${isActive ? "text-brand-600" : "text-slate-500"}`
                }
              >
                <Icon size={18} />
                {label}
              </NavLink>
            ))}
          </div>
        </nav>
      )}
    </>
  );
}
