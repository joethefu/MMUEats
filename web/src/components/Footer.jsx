import { Link } from "react-router-dom";
import { FaFacebook, FaInstagram, FaTwitter } from "react-icons/fa";

const columns = [
  {
    title: "MMUEats",
    links: [
      { label: "Home", to: "/" },
      { label: "About", to: "/about" },
      { label: "Contact", to: "/contact" },
      { label: "Help", to: "/help" },
      { label: "Terms", to: "/terms" },
      { label: "Privacy Policy", to: "/privacy" },
    ],
  },
  {
    title: "Customer",
    links: [
      { label: "Sign Up", to: "/signup" },
      { label: "Login", to: "/login" },
      { label: "Orders", to: "/orders" },
      { label: "Favorites", to: "/favorites" },
      { label: "Help Center", to: "/help" },
    ],
  },
  {
    title: "Become a Partner",
    links: [
      { label: "Become a Vendor", to: "/become-a-vendor" },
      { label: "Become a Delivery Partner", to: "/become-a-delivery-partner" },
    ],
  },
  {
    title: "Support",
    links: [
      { label: "Contact Support", to: "/contact" },
      { label: "FAQs", to: "/help" },
      { label: "Report a Problem", to: "/contact" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
          {columns.map((col) => (
            <div key={col.title}>
              <h3 className="text-sm font-semibold text-brand-700">{col.title}</h3>
              <ul className="mt-4 space-y-2">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link to={link.to} className="text-sm text-slate-600 hover:text-brand-600">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-slate-200 pt-6 sm:flex-row">
          <p className="text-xs text-slate-500">
            &copy; {new Date().getFullYear()} MMUEats — Multimedia University of Kenya. All rights reserved.
          </p>
          <div className="flex gap-4 text-slate-400">
            <a href="#" aria-label="Facebook" className="hover:text-brand-600"><FaFacebook /></a>
            <a href="#" aria-label="Instagram" className="hover:text-brand-600"><FaInstagram /></a>
            <a href="#" aria-label="Twitter" className="hover:text-brand-600"><FaTwitter /></a>
          </div>
        </div>
      </div>
    </footer>
  );
}
