import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { vendorService } from "../../services/vendorService";

const STATUS_OPTIONS = [
  { value: "open", label: "Open" },
  { value: "closed", label: "Closed" },
  { value: "temporarily_unavailable", label: "Temporarily Unavailable" },
];

export default function VendorRestaurantProfilePage() {
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm();
  const [restaurant, setRestaurant] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    vendorService
      .getMyRestaurant()
      .then((data) => {
        setRestaurant(data);
        reset({
          name: data.name,
          description: data.description,
          phone_number: data.phone_number,
          email: data.email,
          location: data.location,
          opening_time: data.opening_time,
          closing_time: data.closing_time,
          status: data.status,
          delivery_fee: data.delivery_fee,
          average_delivery_minutes: data.average_delivery_minutes,
        });
      })
      .catch(() => setRestaurant(null))
      .finally(() => setIsLoading(false));
  }, [reset]);

  const onSubmit = async (values) => {
    const formData = new FormData();
    Object.entries(values).forEach(([key, val]) => {
      if (val instanceof FileList) {
        if (val[0]) formData.append(key, val[0]);
      } else if (val !== undefined && val !== null && val !== "") {
        formData.append(key, val);
      }
    });

    try {
      if (restaurant) {
        const updated = await vendorService.updateRestaurant(restaurant.slug, formData);
        setRestaurant(updated);
        toast.success("Restaurant profile updated");
      } else {
        const created = await vendorService.createRestaurant(formData);
        setRestaurant(created);
        toast.success("Restaurant profile created!");
      }
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || "Couldn't save your restaurant profile.");
    }
  };

  if (isLoading) return <p className="text-slate-500">Loading…</p>;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-900">{restaurant ? "Edit Restaurant Profile" : "Create Your Restaurant"}</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
        <div>
          <label className="block text-sm font-medium text-slate-700">Restaurant Name</label>
          <input {...register("name", { required: "Name is required" })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Description</label>
          <textarea {...register("description")} rows={3} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-700">Location</label>
            <input {...register("location", { required: "Location is required" })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Phone Number</label>
            <input {...register("phone_number")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Email</label>
            <input type="email" {...register("email")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Status</label>
            <select {...register("status")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              {STATUS_OPTIONS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Opening Time</label>
            <input type="time" {...register("opening_time")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Closing Time</label>
            <input type="time" {...register("closing_time")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Delivery Fee (KES)</label>
            <input type="number" step="0.01" {...register("delivery_fee")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Avg. Delivery Time (min)</label>
            <input type="number" {...register("average_delivery_minutes")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-700">Logo</label>
            <input type="file" accept="image/*" {...register("logo")} className="mt-1 w-full text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Banner</label>
            <input type="file" accept="image/*" {...register("banner")} className="mt-1 w-full text-sm" />
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-lg bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {isSubmitting ? "Saving…" : restaurant ? "Save Changes" : "Create Restaurant"}
        </button>
      </form>
    </div>
  );
}
