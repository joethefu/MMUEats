import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { FaStar, FaClock, FaShoppingCart, FaHeart, FaReceipt, FaBell, FaRedo } from "react-icons/fa";
import { useAuth } from "../contexts/AuthContext";
import { useCart } from "../contexts/CartContext";
import { useNotifications } from "../contexts/NotificationContext";
import { restaurantService, mealService } from "../services/restaurantService";
import { orderService } from "../services/orderService";

const STATUS_COLORS = {
  pending: "bg-amber-100 text-amber-700",
  accepted: "bg-blue-100 text-blue-700",
  preparing: "bg-blue-100 text-blue-700",
  ready_for_pickup: "bg-indigo-100 text-indigo-700",
  picked_up: "bg-indigo-100 text-indigo-700",
  out_for_delivery: "bg-purple-100 text-purple-700",
  delivered: "bg-green-100 text-green-700",
  cancelled: "bg-slate-100 text-slate-500",
  rejected: "bg-red-100 text-red-700",
};
const FINISHED = ["delivered", "cancelled", "rejected"];

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
}

function StatTile({ icon: Icon, label, value, to }) {
  return (
    <Link to={to} className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 transition hover:shadow-md">
      <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
        <Icon />
      </span>
      <span>
        <span className="block text-xl font-bold text-slate-900">{value}</span>
        <span className="block text-xs text-slate-500">{label}</span>
      </span>
    </Link>
  );
}

function Section({ title, linkTo, linkLabel = "See all", children }) {
  return (
    <section className="mt-10">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        {linkTo && (
          <Link to={linkTo} className="text-sm font-medium text-brand-600 hover:underline">
            {linkLabel}
          </Link>
        )}
      </div>
      {children}
    </section>
  );
}

const Empty = ({ children }) => <p className="rounded-xl border border-dashed border-slate-300 p-6 text-sm text-slate-500">{children}</p>;

export default function CustomerDashboardPage() {
  const { user } = useAuth();
  const { cart, refreshCart } = useCart();
  const { notifications, unreadCount } = useNotifications();
  const navigate = useNavigate();

  const orders = useQuery({ queryKey: ["dash-orders"], queryFn: () => orderService.list() });
  const topRestaurants = useQuery({
    queryKey: ["dash-restaurants"],
    queryFn: () => restaurantService.list({ ordering: "-average_rating" }),
  });
  const popularMeals = useQuery({
    queryKey: ["dash-meals"],
    queryFn: () => mealService.list({ ordering: "-order_count" }),
  });
  const favorites = useQuery({ queryKey: ["dash-favorites"], queryFn: () => restaurantService.listFavorites() });

  const orderList = orders.data?.results || [];
  const activeOrders = orderList.filter((o) => !FINISHED.includes(o.status));
  const pastOrders = orderList.filter((o) => o.status === "delivered").slice(0, 3);
  const favList = favorites.data?.results || [];
  const cartCount = (cart?.items || []).reduce((n, i) => n + i.quantity, 0);

  const reorder = async (id) => {
    try {
      await orderService.reorder(id);
      await refreshCart();
      toast.success("Items added to your cart");
      navigate("/cart");
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || "Couldn't reorder that one.");
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-bold text-slate-900">
        {greeting()}, {user?.full_name?.split(" ")[0] || "there"} 👋
      </h1>
      <p className="mt-1 text-slate-500">What are you craving on campus today?</p>

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile icon={FaReceipt} label="Total orders" value={orders.data?.count ?? orderList.length} to="/orders" />
        <StatTile icon={FaClock} label="Active orders" value={activeOrders.length} to="/orders" />
        <StatTile icon={FaHeart} label="Favorites" value={favorites.data?.count ?? favList.length} to="/favorites" />
        <StatTile icon={FaShoppingCart} label="Cart items" value={cartCount} to="/cart" />
      </div>

      {activeOrders.length > 0 && (
        <Section title="Active orders" linkTo="/orders">
          <div className="grid gap-4 sm:grid-cols-2">
            {activeOrders.map((o) => (
              <Link key={o.id} to={`/orders/${o.id}`} className="rounded-xl border border-brand-200 bg-brand-50/40 p-4 hover:shadow-md">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-slate-900">{o.restaurant_name}</p>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[o.status]}`}>
                    {o.status.replace(/_/g, " ")}
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-500">#{o.order_number} · KES {o.total}</p>
                <p className="mt-2 text-xs font-medium text-brand-600">Track order →</p>
              </Link>
            ))}
          </div>
        </Section>
      )}

      <Section title="Top-rated restaurants" linkTo="/restaurants">
        {topRestaurants.isLoading ? (
          <p className="text-slate-500">Loading…</p>
        ) : (topRestaurants.data?.results || []).length === 0 ? (
          <Empty>No restaurants yet. Check back soon!</Empty>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {topRestaurants.data.results.slice(0, 3).map((r) => (
              <Link key={r.id} to={`/restaurants/${r.slug}`} className="overflow-hidden rounded-xl border border-slate-200 bg-white hover:shadow-md">
                <div className="flex h-28 items-center justify-center bg-slate-100">
                  {r.logo ? (
                    <img src={r.logo} alt={r.name} className="h-full w-full object-cover" />
                  ) : (
                    <span className="text-3xl font-bold text-brand-200">{r.name[0]}</span>
                  )}
                </div>
                <div className="p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-slate-900">{r.name}</h3>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${r.is_orderable ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
                      {r.is_orderable ? "Open" : "Closed"}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center gap-4 text-xs text-slate-600">
                    <span className="flex items-center gap-1"><FaStar className="text-gold-500" /> {r.average_rating || "New"}</span>
                    <span className="flex items-center gap-1"><FaClock /> ~{r.average_delivery_minutes} min</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Section>

      <Section title="Popular meals on campus">
        {popularMeals.isLoading ? (
          <p className="text-slate-500">Loading…</p>
        ) : (popularMeals.data?.results || []).length === 0 ? (
          <Empty>No meals yet.</Empty>
        ) : (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {popularMeals.data.results.slice(0, 4).map((m) => (
              <Link key={m.id} to={`/restaurants/${m.restaurant_slug}`} className="overflow-hidden rounded-xl border border-slate-200 bg-white hover:shadow-md">
                <div className="flex h-24 items-center justify-center bg-slate-100">
                  {m.image ? (
                    <img src={m.image} alt={m.name} className="h-full w-full object-cover" />
                  ) : (
                    <span className="text-2xl font-bold text-brand-200">{m.name[0]}</span>
                  )}
                </div>
                <div className="p-3">
                  <p className="truncate text-sm font-medium text-slate-900">{m.name}</p>
                  <p className="truncate text-xs text-slate-500">{m.restaurant_name}</p>
                  <p className="mt-1 text-sm font-semibold text-brand-600">
                    KES {m.discounted_price}
                    {Number(m.discount_percentage) > 0 && (
                      <span className="ml-1 text-xs font-normal text-slate-400 line-through">{m.price}</span>
                    )}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Section>

      <Section title="Order again" linkTo="/orders" linkLabel="Order history">
        {pastOrders.length === 0 ? (
          <Empty>Your delivered orders will show up here for one-tap reordering.</Empty>
        ) : (
          <div className="space-y-3">
            {pastOrders.map((o) => (
              <div key={o.id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4">
                <Link to={`/orders/${o.id}`} className="min-w-0">
                  <p className="font-medium text-slate-900">{o.restaurant_name}</p>
                  <p className="truncate text-sm text-slate-500">
                    {(o.items || []).map((i) => `${i.quantity}× ${i.meal_name}`).join(", ")} · KES {o.total}
                  </p>
                </Link>
                <button
                  onClick={() => reorder(o.id)}
                  className="ml-4 flex shrink-0 items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
                >
                  <FaRedo size={12} /> Reorder
                </button>
              </div>
            ))}
          </div>
        )}
      </Section>

      <div className="grid gap-8 lg:grid-cols-2">
        <Section title="Favorites" linkTo="/favorites">
          {favList.length === 0 ? (
            <Empty>Tap the heart on a restaurant to save it here.</Empty>
          ) : (
            <ul className="space-y-2">
              {favList.slice(0, 4).map((f) => (
                <li key={f.id}>
                  <Link to={`/restaurants/${f.restaurant_detail.slug}`} className="block rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 hover:shadow-sm">
                    {f.restaurant_detail.name}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title={`Notifications${unreadCount ? ` (${unreadCount} new)` : ""}`}>
          {notifications.length === 0 ? (
            <Empty>You're all caught up.</Empty>
          ) : (
            <ul className="space-y-2">
              {notifications.slice(0, 4).map((n) => (
                <li key={n.id} className={`flex gap-3 rounded-lg border px-4 py-3 text-sm ${n.is_read ? "border-slate-200 bg-white" : "border-brand-200 bg-brand-50/40"}`}>
                  <FaBell className="mt-0.5 shrink-0 text-brand-500" />
                  <span>
                    <span className="block font-medium text-slate-900">{n.title}</span>
                    <span className="block text-slate-500">{n.message}</span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Section>
      </div>
    </div>
  );
}
