import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <div>
      <section className="bg-gradient-to-b from-brand-50 to-white px-4 py-20 text-center sm:px-6">
        <h1 className="mx-auto max-w-2xl text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
          Campus food, delivered to your <span className="text-brand-600">hostel</span>.
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-slate-600">
          Order from MMU's favorite cafeterias and restaurants — track it live, all the way to your door.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to="/signup" className="rounded-lg bg-brand-600 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-700">
            Get Started
          </Link>
          <Link to="/restaurants" className="rounded-lg border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            Browse Restaurants
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="grid gap-8 sm:grid-cols-3">
          {[
            { title: "Browse", desc: "Explore menus from campus vendors near you." },
            { title: "Order & Pay", desc: "Checkout securely with M-Pesa or cash on delivery." },
            { title: "Track", desc: "Watch your order move from kitchen to your hostel in real time." },
          ].map((s) => (
            <div key={s.title} className="rounded-xl border border-slate-200 p-6 text-center">
              <h3 className="font-semibold text-brand-700">{s.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
