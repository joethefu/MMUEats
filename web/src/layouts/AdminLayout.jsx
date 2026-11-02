import { NavLink, Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";

const links = [
  { to: "/admin/dashboard", label: "Dashboard" },
  { to: "/admin/applications", label: "Applications" },
  { to: "/admin/users", label: "Users" },
  { to: "/admin/advertisements", label: "Advertisements" },
  // Promotions and a dedicated Reports view can be added here as they grow.
];

export default function AdminLayout() {
  return (
    <div className="flex min-h-screen flex-col pb-16 md:pb-0">
      <Navbar />
      <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-6 px-4 py-6 sm:px-6 md:flex-row">
        <aside className="shrink-0 md:w-56">
          <nav className="flex gap-2 overflow-x-auto md:flex-col md:overflow-visible">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium ${
                    isActive ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-100"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
        </aside>
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
