import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { advertisementService } from "../../services/advertisementService";

const PLACEMENTS = [
  { value: "startup_popup", label: "Startup Popup" },
  { value: "homepage_banner", label: "Homepage Banner" },
  { value: "promotional_section", label: "Promotional Section" },
];

export default function AdminAdvertisementsPage() {
  const [ads, setAds] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingAd, setEditingAd] = useState(null); // null = hidden, {} = creating, {...} = editing
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm();

  const load = () => advertisementService.adminList().then((data) => setAds(data.results || data));

  useEffect(() => {
    load().finally(() => setIsLoading(false));
  }, []);

  const openCreate = () => {
    reset({ title: "", description: "", cta_label: "", external_url: "", placement: "startup_popup", start_date: "", end_date: "", priority: 0, is_active: true });
    setEditingAd({});
  };

  const openEdit = (ad) => {
    reset({
      title: ad.title, description: ad.description || "", cta_label: ad.cta_label || "", external_url: ad.external_url, placement: ad.placement,
      start_date: ad.start_date, end_date: ad.end_date, priority: ad.priority, is_active: ad.is_active,
    });
    setEditingAd(ad);
  };

  const onSubmit = async (values) => {
    const formData = new FormData();
    Object.entries(values).forEach(([key, val]) => {
      if (key === "image") {
        if (val?.[0]) formData.append("image", val[0]);
      } else if (val !== undefined && val !== null) {
        formData.append(key, val);
      }
    });

    try {
      if (editingAd?.id) {
        await advertisementService.update(editingAd.id, formData);
        toast.success("Advertisement updated");
      } else {
        await advertisementService.create(formData);
        toast.success("Advertisement created");
      }
      setEditingAd(null);
      load();
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || "Couldn't save this advertisement.");
    }
  };

  const handleDelete = async (ad) => {
    if (!confirm(`Delete "${ad.title}"?`)) return;
    try {
      await advertisementService.remove(ad.id);
      toast.success("Advertisement deleted");
      load();
    } catch {
      toast.error("Couldn't delete this advertisement.");
    }
  };

  const handleToggleActive = async (ad) => {
    try {
      const formData = new FormData();
      formData.append("is_active", !ad.is_active);
      await advertisementService.update(ad.id, formData);
      load();
    } catch {
      toast.error("Couldn't update this advertisement.");
    }
  };

  if (isLoading) return <p className="text-slate-500">Loading…</p>;

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Advertisements</h1>
        <button onClick={openCreate} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
          + New Advertisement
        </button>
      </div>

      {editingAd !== null && (
        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4 rounded-xl border border-slate-200 p-4" noValidate>
          <h2 className="font-semibold text-slate-900">{editingAd.id ? "Edit Advertisement" : "New Advertisement"}</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700">Title</label>
              <input {...register("title", { required: true })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Description (optional)</label>
              <input {...register("description")} maxLength={255} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Button text (optional)</label>
              <input {...register("cta_label")} maxLength={40} placeholder="e.g. Order now" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Link (optional)</label>
              <input {...register("external_url")} placeholder="/restaurants/my-vendor  or  https://example.com" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              <p className="mt-1 text-xs text-slate-500">Use a path for pages inside MMUEats (e.g. /restaurants/kitchen-slug) or a full https:// URL.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Placement</label>
              <select {...register("placement")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                {PLACEMENTS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Priority</label>
              <input type="number" {...register("priority")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Start Date</label>
              <input type="date" {...register("start_date", { required: true })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">End Date</label>
              <input type="date" {...register("end_date", { required: true })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Image {editingAd.id ? "(leave blank to keep current)" : ""}</label>
              <input type="file" accept="image/*" {...register("image", { required: !editingAd.id })} className="mt-1 w-full text-sm" />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input type="checkbox" {...register("is_active")} id="is_active" />
              <label htmlFor="is_active" className="text-sm text-slate-700">Active</label>
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={isSubmitting} className="rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
              {isSubmitting ? "Saving…" : "Save"}
            </button>
            <button type="button" onClick={() => setEditingAd(null)} className="rounded-lg border border-slate-300 px-5 py-2 text-sm font-medium text-slate-700">
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="mt-6 divide-y divide-slate-200 rounded-xl border border-slate-200">
        {ads.length === 0 && <p className="p-4 text-sm text-slate-500">No advertisements yet.</p>}
        {ads.map((ad) => (
          <div key={ad.id} className="flex items-center justify-between gap-4 p-4">
            <div>
              <p className="font-medium text-slate-900">
                {ad.title}{" "}
                <span className={`ml-2 rounded-full px-2 py-0.5 text-xs font-medium ${ad.is_active ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
                  {ad.is_active ? "Active" : "Inactive"}
                </span>
                {ad.is_currently_valid && <span className="ml-2 rounded-full bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-700">Live now</span>}
              </p>
              <p className="text-sm text-slate-500">
                {PLACEMENTS.find((p) => p.value === ad.placement)?.label} · {ad.start_date} → {ad.end_date} · Priority {ad.priority}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {ad.impressions_count} impressions · {ad.clicks_count} clicks
                {ad.impressions_count > 0 && ` · ${((ad.clicks_count / ad.impressions_count) * 100).toFixed(1)}% CTR`}
              </p>
            </div>
            <div className="flex shrink-0 gap-2 text-sm">
              <button onClick={() => handleToggleActive(ad)} className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-50">
                {ad.is_active ? "Deactivate" : "Activate"}
              </button>
              <button onClick={() => openEdit(ad)} className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-50">Edit</button>
              <button onClick={() => handleDelete(ad)} className="rounded-lg border border-red-300 px-3 py-1.5 text-red-600 hover:bg-red-50">Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
