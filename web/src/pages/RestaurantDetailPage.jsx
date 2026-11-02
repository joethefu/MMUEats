import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { FaStar, FaClock } from "react-icons/fa";
import { restaurantService } from "../services/restaurantService";
import MealCard from "../components/MealCard";
import FavoriteButton from "../components/FavoriteButton";
import ReviewsSection from "../components/ReviewsSection";

const vendorFavApi = { add: (id) => restaurantService.favorite(id), remove: (favId) => restaurantService.unfavorite(favId) };

export default function RestaurantDetailPage() {
  const { slug } = useParams();
  const [restaurant, setRestaurant] = useState(null);
  const [meals, setMeals] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadRestaurant = () => restaurantService.get(slug).then(setRestaurant);

  useEffect(() => {
    setIsLoading(true);
    restaurantService
      .get(slug)
      .then(async (r) => {
        setRestaurant(r);
        const mealData = await restaurantService.listMeals(r.id);
        setMeals(mealData.results || []);
        setError(null);
      })
      .catch(() => setError("Couldn't load this restaurant."))
      .finally(() => setIsLoading(false));
  }, [slug]);

  if (isLoading) return <div className="mx-auto max-w-5xl px-4 py-16 text-slate-500">Loading…</div>;
  if (error || !restaurant) return <div className="mx-auto max-w-5xl px-4 py-16 text-red-600">{error || "Not found."}</div>;

  return (
    <div>
      <div className="h-40 w-full bg-slate-100 sm:h-48">
        {restaurant.banner && <img src={restaurant.banner} alt="" className="h-full w-full object-cover" />}
      </div>

      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-2xl font-bold text-slate-900">{restaurant.name}</h1>
            <p className="mt-1 text-sm text-slate-500">{restaurant.location}</p>
            <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-600">
              <span className="flex items-center gap-1">
                <FaStar className="text-gold-500" /> {Number(restaurant.average_rating) ? Number(restaurant.average_rating).toFixed(1) : "New"} ({restaurant.ratings_count})
              </span>
              <span className="flex items-center gap-1"><FaClock /> ~{restaurant.average_delivery_minutes} min</span>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${restaurant.is_orderable ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
                {restaurant.is_orderable ? "Open now" : "Currently closed"}
              </span>
            </div>
          </div>
          <FavoriteButton
            itemId={restaurant.id}
            isFavorited={restaurant.is_favorited}
            favoriteId={restaurant.favorite_id}
            api={vendorFavApi}
            className="border border-slate-200"
            size={20}
          />
        </div>

        {restaurant.description && <p className="mt-4 text-sm text-slate-600">{restaurant.description}</p>}

        <h2 className="mt-10 text-lg font-bold text-slate-900">Menu</h2>
        {meals.length === 0 ? (
          <p className="mt-4 text-slate-500">This restaurant hasn't added any meals yet.</p>
        ) : (
          <div className="mt-4 grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3">
            {meals.map((meal) => <MealCard key={meal.id} meal={meal} />)}
          </div>
        )}

        <ReviewsSection
          targetId={restaurant.id}
          api={{
            list: (id) => restaurantService.listReviews(id),
            submit: (v) => restaurantService.submitReview({ restaurant: restaurant.id, ...v }),
          }}
          onChanged={loadRestaurant}
          title="Vendor ratings & reviews"
        />
      </div>
    </div>
  );
}
