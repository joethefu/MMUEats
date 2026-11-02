import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { FaStar, FaClock } from "react-icons/fa";
import { restaurantService, mealService } from "../services/restaurantService";
import BannerCarousel from "../components/BannerCarousel";
import CategoryChips from "../components/CategoryChips";
import MealCard from "../components/MealCard";
import FavoriteButton from "../components/FavoriteButton";

const vendorFavApi = { add: (id) => restaurantService.favorite(id), remove: (favId) => restaurantService.unfavorite(favId) };

export default function RestaurantsPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") || "";

  const [categories, setCategories] = useState([]);
  const [category, setCategory] = useState("");
  const [meals, setMeals] = useState([]);
  const [mealPage, setMealPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [mealsLoading, setMealsLoading] = useState(true);
  const [mealsError, setMealsError] = useState(null);
  const [vendors, setVendors] = useState([]);
  const [vendorsLoading, setVendorsLoading] = useState(true);

  useEffect(() => {
    mealService.listCategories().then((d) => setCategories(Array.isArray(d) ? d : d.results || [])).catch(() => {});
  }, []);

  // Meals: reload from page 1 whenever the category or search term changes.
  useEffect(() => {
    let cancelled = false;
    setMealsLoading(true);
    mealService
      .list({ ...(category ? { category } : {}), ...(q ? { search: q } : {}), ordering: "-order_count", page: 1 })
      .then((d) => {
        if (cancelled) return;
        setMeals(d.results || []);
        setHasMore(!!d.next);
        setMealPage(1);
        setMealsError(null);
      })
      .catch(() => !cancelled && setMealsError("Couldn't load the menu right now."))
      .finally(() => !cancelled && setMealsLoading(false));
    return () => { cancelled = true; };
  }, [category, q]);

  useEffect(() => {
    let cancelled = false;
    setVendorsLoading(true);
    restaurantService
      .list(q ? { search: q } : {})
      .then((d) => !cancelled && setVendors(d.results || []))
      .catch(() => !cancelled && setVendors([]))
      .finally(() => !cancelled && setVendorsLoading(false));
    return () => { cancelled = true; };
  }, [q]);

  const loadMore = async () => {
    const next = mealPage + 1;
    const d = await mealService.list({ ...(category ? { category } : {}), ...(q ? { search: q } : {}), ordering: "-order_count", page: next });
    setMeals((m) => [...m, ...(d.results || [])]);
    setHasMore(!!d.next);
    setMealPage(next);
  };

  return (
    <div>
      <BannerCarousel />
      <CategoryChips categories={categories} selected={category} onSelect={setCategory} />

      <div className="mx-auto max-w-7xl px-4 pb-10 sm:px-6 lg:px-8">
        {q && (
          <p className="mb-4 text-sm text-slate-600">
            Results for <span className="font-semibold">“{q}”</span>{" "}
            <button onClick={() => setParams({})} className="ml-2 text-brand-600 hover:underline">Clear</button>
          </p>
        )}

        <h2 className="text-lg font-bold text-slate-900">{category ? categories.find((c) => String(c.id) === String(category))?.name : "All food"}</h2>
        {mealsLoading && <p className="mt-4 text-slate-500">Loading menu…</p>}
        {mealsError && <p className="mt-4 text-red-600">{mealsError}</p>}
        {!mealsLoading && !mealsError && meals.length === 0 && (
          <p className="mt-4 text-slate-500">{q ? "No food matches your search." : "No meals available in this category yet."}</p>
        )}
        <div className="mt-4 grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-4">
          {meals.map((m) => <MealCard key={m.id} meal={m} />)}
        </div>
        {hasMore && (
          <div className="mt-6 text-center">
            <button onClick={loadMore} className="rounded-lg border border-slate-300 px-6 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
              Load more
            </button>
          </div>
        )}

        <h2 className="mt-12 text-lg font-bold text-slate-900">Vendors</h2>
        {vendorsLoading && <p className="mt-4 text-slate-500">Loading vendors…</p>}
        {!vendorsLoading && vendors.length === 0 && <p className="mt-4 text-slate-500">No vendors found.</p>}
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {vendors.map((r) => (
            <div key={r.id} className="relative overflow-hidden rounded-xl border border-slate-200 bg-white transition hover:shadow-md">
              <Link to={`/restaurants/${r.slug}`} className="block">
                <div className="flex h-32 items-center justify-center bg-slate-100 text-slate-400">
                  {r.logo ? <img src={r.logo} alt={r.name} className="h-full w-full object-cover" /> : <span className="text-3xl font-bold text-brand-200">{r.name[0]}</span>}
                </div>
                <div className="p-4">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="truncate font-semibold text-slate-900">{r.name}</h3>
                    <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${r.is_orderable ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
                      {r.is_orderable ? "Open" : "Closed"}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-slate-500">{r.location}</p>
                  <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-600">
                    <span className="flex items-center gap-1"><FaStar className="text-gold-500" /> {Number(r.average_rating) ? Number(r.average_rating).toFixed(1) : "New"}{r.ratings_count > 0 && ` (${r.ratings_count})`}</span>
                    <span className="flex items-center gap-1"><FaClock /> ~{r.average_delivery_minutes} min</span>
                    <span>KES {r.delivery_fee} delivery</span>
                  </div>
                </div>
              </Link>
              <FavoriteButton itemId={r.id} isFavorited={r.is_favorited} favoriteId={r.favorite_id} api={vendorFavApi} className="absolute right-2 top-2" size={15} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
