import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { vendorService } from "../../services/vendorService";

export default function VendorMenuPage() {
  const [restaurant, setRestaurant] = useState(null);
  const [meals, setMeals] = useState([]);
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingMeal, setEditingMeal] = useState(null); // null = not editing, {} = creating, {...} = editing
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm();

  const loadMeals = (restaurantId) => {
    vendorService.listMyMeals(restaurantId).then((data) => setMeals(data.results || []));
  };

  useEffect(() => {
    Promise.all([vendorService.getMyRestaurant(), vendorService.listCategories()])
      .then(([r, cats]) => {
        setRestaurant(r);
        setCategories(cats.results || []);
        loadMeals(r.id);
      })
      .catch(() => setRestaurant(null))
      .finally(() => setIsLoading(false));
  }, []);

  const openCreate = () => {
    reset({ name: "", price: "", category: "", description: "", is_available: true, preparation_time_minutes: 15, discount_percentage: 0, packaging_fee: 0 });
    setEditingMeal({});
  };

  const openEdit = (meal) => {
    reset({
      name: meal.name, price: meal.price, category: meal.category || "",
      description: meal.description, is_available: meal.is_available,
      preparation_time_minutes: meal.preparation_time_minutes, discount_percentage: meal.discount_percentage,
      packaging_fee: meal.packaging_fee,
    });
    setEditingMeal(meal);
  };

  const onSubmit = async (values) => {
    try {
      if (editingMeal?.id) {
        await vendorService.updateMeal(editingMeal.id, values);
        toast.success("Meal updated");
      } else {
        await vendorService.createMeal(values);
        toast.success("Meal added");
      }
      setEditingMeal(null);
      loadMeals(restaurant.id);
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || "Couldn't save this meal.");
    }
  };

  const handleToggleAvailable = async (meal) => {
    try {
      await vendorService.updateMeal(meal.id, { is_available: !meal.is_available });
      loadMeals(restaurant.id);
    } catch {
      toast.error("Couldn't update availability.");
    }
  };

  const handleDelete = async (meal) => {
    if (!confirm(`Delete "${meal.name}"?`)) return;
    try {
      await vendorService.deleteMeal(meal.id);
      toast.success("Meal deleted");
      loadMeals(restaurant.id);
    } catch {
      toast.error("Couldn't delete this meal.");
    }
  };

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (!restaurant) return <p className="text-slate-500">Set up your restaurant profile first.</p>;

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Menu</h1>
        <button onClick={openCreate} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
          + Add Meal
        </button>
      </div>

      {editingMeal !== null && (
        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4 rounded-xl border border-slate-200 p-4" noValidate>
          <h2 className="font-semibold text-slate-900">{editingMeal.id ? "Edit Meal" : "New Meal"}</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700">Name</label>
              <input {...register("name", { required: true })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Price (KES)</label>
              <input type="number" step="0.01" {...register("price", { required: true })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Category</label>
              <select {...register("category")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                <option value="">None</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Discount %</label>
              <input type="number" {...register("discount_percentage")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Container fee (KES, per item)</label>
              <input type="number" min="0" step="0.01" {...register("packaging_fee")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Prep Time (min)</label>
              <input type="number" {...register("preparation_time_minutes")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input type="checkbox" {...register("is_available")} id="is_available" />
              <label htmlFor="is_available" className="text-sm text-slate-700">Available</label>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Description</label>
            <textarea {...register("description")} rows={2} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={isSubmitting} className="rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
              {isSubmitting ? "Saving…" : "Save"}
            </button>
            <button type="button" onClick={() => setEditingMeal(null)} className="rounded-lg border border-slate-300 px-5 py-2 text-sm font-medium text-slate-700">
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="mt-6 divide-y divide-slate-200 rounded-xl border border-slate-200">
        {meals.length === 0 && <p className="p-4 text-sm text-slate-500">No meals yet — add your first one.</p>}
        {meals.map((meal) => (
          <div key={meal.id} className="flex items-center justify-between gap-4 p-4">
            <div>
              <p className="font-medium text-slate-900">{meal.name}</p>
              <p className="text-sm text-slate-500">KES {meal.discounted_price} · {meal.is_available ? "Available" : "Unavailable"}</p>
            </div>
            <div className="flex gap-2 text-sm">
              <button onClick={() => handleToggleAvailable(meal)} className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-50">
                {meal.is_available ? "Mark Unavailable" : "Mark Available"}
              </button>
              <button onClick={() => openEdit(meal)} className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-50">Edit</button>
              <button onClick={() => handleDelete(meal)} className="rounded-lg border border-red-300 px-3 py-1.5 text-red-600 hover:bg-red-50">Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
