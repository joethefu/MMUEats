import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { restaurantService, mealService } from "../services/restaurantService";
import MealCard from "../components/MealCard";
import FavoriteButton from "../components/FavoriteButton";

const vendorFavApi = { add: (id) => restaurantService.favorite(id), remove: (favId) => restaurantService.unfavorite(favId) };

export default function FavoritesPage() {
  const [tab, setTab] = useState("meals");
  const [vendors, setVendors] = useState([]);
  const [meals, setMeals] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([restaurantService.listFavorites(), mealService.listFavorites()])
      .then(([v, m]) => {
        setVendors(v.results || []);
        setMeals(m.results || []);
      })
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <div className="mx-auto max-w-3xl px-4 py-16 text-slate-500">Loading favorites…</div>;

  const tabBtn = (id, label, count) => (
    <button
      onClick={() => setTab(id)}
      className={`rounded-full px-4 py-1.5 text-sm font-medium ${tab === id ? "bg-brand-600 text-white" : "border border-slate-200 text-slate-700 hover:border-brand-400"}`}
    >
      {label} ({count})
    </button>
  );

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-bold text-slate-900">Your Favorites</h1>
      <div className="mt-4 flex gap-2">
        {tabBtn("meals", "Food", meals.length)}
        {tabBtn("vendors", "Vendors", vendors.length)}
      </div>

      {tab === "meals" ? (
        meals.length === 0 ? (
          <p className="mt-8 text-slate-500">No favorite food yet. Tap the heart on any meal to save it.</p>
        ) : (
          <div className="mt-6 grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-4">
            {meals.map((f) => (
              <MealCard key={f.id} meal={{ ...f.meal_detail, is_favorited: true, favorite_id: f.id }} />
            ))}
          </div>
        )
      ) : vendors.length === 0 ? (
        <p className="mt-8 text-slate-500">No favorite vendors yet.</p>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {vendors.map((fav) => (
            <div key={fav.id} className="relative rounded-xl border border-slate-200 bg-white p-4 hover:shadow-sm">
              <Link to={`/restaurants/${fav.restaurant_detail.slug}`} className="block pr-10">
                <p className="font-medium text-slate-900">{fav.restaurant_detail.name}</p>
                <p className="text-sm text-slate-500">{fav.restaurant_detail.location}</p>
              </Link>
              <FavoriteButton itemId={fav.restaurant} isFavorited favoriteId={fav.id} api={vendorFavApi} className="absolute right-3 top-3 border border-slate-200" size={15}
                onChange={(on) => !on && setVendors((v) => v.filter((x) => x.id !== fav.id))} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
