import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { FaStar, FaPlus } from "react-icons/fa";
import { mealService } from "../services/restaurantService";
import FavoriteButton from "./FavoriteButton";
import QuantityStepper from "./QuantityStepper";
import { useMealCart } from "../hooks/useMealCart";

const mealFavApi = { add: (id) => mealService.favorite(id), remove: (favId) => mealService.unfavorite(favId) };

export default function MealCard({ meal }) {
  const { quantityOf, setQuantity } = useMealCart();
  const qty = quantityOf(meal.id);
  const discounted = Number(meal.discount_percentage) > 0;

  return (
    <div className="group relative overflow-hidden rounded-xl border border-slate-200 bg-white transition hover:shadow-md">
      <Link to={`/meals/${meal.id}`} className="block">
        <div className="relative aspect-[4/3] w-full bg-slate-100">
          {meal.image ? (
            <img src={meal.image} alt={meal.name} loading="lazy" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-4xl font-bold text-brand-200">{meal.name[0]}</div>
          )}
          {discounted && (
            <span className="absolute left-2 top-2 rounded-full bg-brand-600 px-2 py-0.5 text-xs font-semibold text-white">
              -{meal.discount_percentage}%
            </span>
          )}
        </div>
        <div className="p-3">
          <h3 className="truncate font-semibold text-slate-900">{meal.name}</h3>
          <p className="truncate text-xs text-slate-500">{meal.restaurant_name}</p>
          <div className="mt-1 flex items-center gap-1 text-xs text-slate-600">
            <FaStar className="text-gold-500" /> {Number(meal.average_rating) ? Number(meal.average_rating).toFixed(1) : "New"}
            {meal.ratings_count > 0 && <span className="text-slate-400">({meal.ratings_count})</span>}
          </div>
          <p className="mt-1 text-sm font-semibold text-brand-600">
            KES {meal.discounted_price}
            {discounted && <span className="ml-1 text-xs font-normal text-slate-400 line-through">{meal.price}</span>}
          </p>
        </div>
      </Link>

      <FavoriteButton
        itemId={meal.id}
        isFavorited={meal.is_favorited}
        favoriteId={meal.favorite_id}
        api={mealFavApi}
        className="absolute right-2 top-2"
        size={15}
      />

      <div className="flex items-center justify-between px-3 pb-3">
        {!meal.is_available ? (
          <span className="text-xs font-medium text-red-500">Unavailable</span>
        ) : qty > 0 ? (
          <QuantityStepper size="sm" value={qty} max={meal.stock_quantity ?? 99} onChange={(n) => setQuantity(meal, n)} />
        ) : (
          <button
            onClick={async () => (await setQuantity(meal, 1)) && toast.success(`Added ${meal.name}`)}
            className="flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-700"
          >
            <FaPlus size={10} /> Add
          </button>
        )}
      </div>
    </div>
  );
}
