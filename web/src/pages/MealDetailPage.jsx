import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { FaStar, FaClock, FaArrowLeft } from "react-icons/fa";
import { mealService } from "../services/restaurantService";
import { useMealCart } from "../hooks/useMealCart";
import QuantityStepper from "../components/QuantityStepper";
import FavoriteButton from "../components/FavoriteButton";
import ReviewsSection from "../components/ReviewsSection";

const mealFavApi = { add: (id) => mealService.favorite(id), remove: (favId) => mealService.unfavorite(favId) };

export default function MealDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { quantityOf, itemFor, setQuantity } = useMealCart();
  const [meal, setMeal] = useState(null);
  const [error, setError] = useState(null);
  const [qty, setQty] = useState(1);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () =>
    mealService.get(id).then(setMeal).catch(() => setError("We couldn't find this meal."));

  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [id]);

  const inCart = meal ? quantityOf(meal.id) : 0;
  useEffect(() => {
    if (!meal) return;
    const existing = itemFor(meal.id);
    setQty(existing ? existing.quantity : 1);
    setNote(existing?.special_instructions || "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meal?.id, inCart]);

  if (error) return <div className="mx-auto max-w-3xl px-4 py-16 text-red-600">{error}</div>;
  if (!meal) return <div className="mx-auto max-w-3xl px-4 py-16 text-slate-500">Loading…</div>;

  const discounted = Number(meal.discount_percentage) > 0;
  const unit = Number(meal.discounted_price) + Number(meal.packaging_fee || 0);
  const maxQty = meal.stock_quantity ?? 99;
  const canOrder = meal.is_available && (meal.stock_quantity == null || meal.stock_quantity > 0);

  const add = async () => {
    setSaving(true);
    const ok = await setQuantity(meal, qty, note);
    setSaving(false);
    if (ok) {
      toast.success(inCart ? "Cart updated" : `Added ${qty} × ${meal.name} to cart`);
    }
  };

  const nutrition = [
    ["Calories", meal.calories && `${meal.calories} kcal`],
    ["Protein", meal.protein_grams && `${meal.protein_grams} g`],
    ["Carbs", meal.carbs_grams && `${meal.carbs_grams} g`],
    ["Fat", meal.fat_grams && `${meal.fat_grams} g`],
  ].filter(([, v]) => v);

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8">
      <button onClick={() => navigate(-1)} className="mb-4 flex items-center gap-2 text-sm text-slate-600 hover:text-brand-600">
        <FaArrowLeft size={12} /> Back
      </button>

      <div className="grid gap-6 md:grid-cols-2 md:gap-10">
        <div className="relative aspect-square w-full overflow-hidden rounded-2xl bg-slate-100 md:aspect-[4/3]">
          {meal.image ? (
            <img src={meal.image} alt={meal.name} className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-6xl font-bold text-brand-200">{meal.name[0]}</div>
          )}
          {discounted && <span className="absolute left-3 top-3 rounded-full bg-brand-600 px-3 py-1 text-sm font-semibold text-white">-{meal.discount_percentage}%</span>}
          <FavoriteButton itemId={meal.id} isFavorited={meal.is_favorited} favoriteId={meal.favorite_id} api={mealFavApi} className="absolute right-3 top-3" size={20} />
        </div>

        <div>
          {meal.category_name && <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">{meal.category_name}</span>}
          <h1 className="mt-2 text-2xl font-bold text-slate-900 sm:text-3xl">{meal.name}</h1>
          <Link to={`/restaurants/${meal.restaurant_slug}`} className="mt-1 inline-block text-sm text-brand-600 hover:underline">{meal.restaurant_name}</Link>

          <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-slate-600">
            <span className="flex items-center gap-1"><FaStar className="text-gold-500" /> {Number(meal.average_rating) ? Number(meal.average_rating).toFixed(1) : "New"}{meal.ratings_count > 0 && ` (${meal.ratings_count} reviews)`}</span>
            <span className="flex items-center gap-1"><FaClock /> ~{meal.preparation_time_minutes} min prep</span>
          </div>

          <p className="mt-4 text-2xl font-bold text-brand-600">
            KES {meal.discounted_price}
            {discounted && <span className="ml-2 text-base font-normal text-slate-400 line-through">KES {meal.price}</span>}
          </p>
          {Number(meal.packaging_fee) > 0 && <p className="text-sm text-slate-500">+ KES {meal.packaging_fee} container fee per item</p>}

          {meal.description && <p className="mt-4 text-slate-700">{meal.description}</p>}
          {meal.ingredients && (
            <div className="mt-4">
              <h2 className="text-sm font-semibold text-slate-900">Ingredients</h2>
              <p className="text-sm text-slate-600">{meal.ingredients}</p>
            </div>
          )}
          {nutrition.length > 0 && (
            <dl className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {nutrition.map(([k, v]) => (
                <div key={k} className="rounded-lg bg-slate-50 p-2 text-center">
                  <dt className="text-xs text-slate-500">{k}</dt>
                  <dd className="text-sm font-semibold text-slate-900">{v}</dd>
                </div>
              ))}
            </dl>
          )}
          {meal.stock_quantity != null && meal.stock_quantity > 0 && meal.stock_quantity <= 10 && (
            <p className="mt-3 text-sm font-medium text-amber-600">Only {meal.stock_quantity} left</p>
          )}

          <div className="mt-6 rounded-xl border border-slate-200 p-4">
            {canOrder ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-700">Quantity</span>
                  <QuantityStepper value={qty} onChange={setQty} max={maxQty} />
                </div>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  maxLength={255}
                  rows={2}
                  placeholder="Special instructions (e.g. no onions)"
                  className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                />
                <button
                  onClick={add}
                  disabled={saving}
                  className="mt-3 w-full rounded-lg bg-brand-600 px-4 py-3 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
                >
                  {inCart ? "Update cart" : "Add to cart"} · KES {(unit * qty).toFixed(2)}
                </button>
                {inCart > 0 && <Link to="/cart" className="mt-2 block text-center text-sm font-medium text-brand-600 hover:underline">View cart</Link>}
              </>
            ) : (
              <p className="text-center text-sm font-medium text-red-500">This item is currently unavailable.</p>
            )}
          </div>
        </div>
      </div>

      <ReviewsSection
        targetId={meal.id}
        api={{ list: (mid) => mealService.listReviews(mid), submit: (v) => mealService.submitReview({ meal: meal.id, ...v }) }}
        onChanged={load}
        title="Ratings & reviews"
      />
    </div>
  );
}
