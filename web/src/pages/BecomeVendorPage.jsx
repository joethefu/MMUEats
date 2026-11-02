import { useState } from "react";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import apiClient from "../services/apiClient";

const faqs = [
  { q: "How long does approval take?", a: "Our team typically reviews applications within 2–3 business days." },
  { q: "Is there a listing fee?", a: "No signup fee. MMUEats takes a small commission per completed order." },
  { q: "Can I update my menu anytime?", a: "Yes — you have full control over your menu, prices, and availability from your vendor dashboard." },
];

export default function BecomeVendorPage() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm();
  const [submitted, setSubmitted] = useState(false);

  const onSubmit = async (values) => {
    try {
      await apiClient.post("/users/vendor-applications/", values);
      setSubmitted(true);
      toast.success("Application submitted!");
    } catch {
      toast.error("Could not submit your application. Please try again.");
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold text-slate-900">Become a Vendor on MMUEats</h1>
      <p className="mt-3 text-slate-600">
        MMUEats connects campus cafeterias, restaurants, and food businesses with thousands of hungry
        students and staff at Multimedia University of Kenya. Reach more customers, manage orders in
        real time, and grow your business — all from one dashboard.
      </p>

      <div className="mt-10 grid gap-8 sm:grid-cols-2">
        <div>
          <h2 className="font-semibold text-slate-900">Who can become a vendor?</h2>
          <p className="mt-2 text-sm text-slate-600">
            Campus cafeterias, licensed restaurants, and approved nearby food businesses serving the MMU community.
          </p>
        </div>
        <div>
          <h2 className="font-semibold text-slate-900">Benefits</h2>
          <ul className="mt-2 list-disc pl-5 text-sm text-slate-600 space-y-1">
            <li>Access to the whole MMU student and staff population</li>
            <li>Real-time order and revenue dashboard</li>
            <li>Flexible menu and pricing control</li>
          </ul>
        </div>
        <div>
          <h2 className="font-semibold text-slate-900">Requirements</h2>
          <ul className="mt-2 list-disc pl-5 text-sm text-slate-600 space-y-1">
            <li>Valid business registration or cafeteria authorization</li>
            <li>A working phone number and email</li>
            <li>Ability to consistently prepare orders within your stated time</li>
          </ul>
        </div>
        <div>
          <h2 className="font-semibold text-slate-900">Approval process</h2>
          <p className="mt-2 text-sm text-slate-600">
            Submit the form below → our admin team reviews it → you're notified by email once approved
            and can log in to set up your menu.
          </p>
        </div>
      </div>

      <h2 className="mt-12 text-xl font-bold text-slate-900">Apply as a Vendor</h2>

      {submitted ? (
        <p className="mt-4 rounded-lg bg-green-50 border border-green-200 p-4 text-sm text-green-800">
          Thanks! We've received your application and will email you once it's reviewed.
        </p>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700">Business/Restaurant Name</label>
              <input {...register("business_name", { required: true })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Owner/Manager Name</label>
              <input {...register("owner_name", { required: true })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Email</label>
              <input type="email" {...register("email", { required: true })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Phone Number</label>
              <input {...register("phone_number", { required: true })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Business Location</label>
              <input {...register("business_location", { required: true })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Food Categories</label>
              <input placeholder="e.g. Fast Food, Vegetarian" {...register("food_categories")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Description</label>
            <textarea {...register("description")} rows={3} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <button type="submit" disabled={isSubmitting} className="rounded-lg bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
            {isSubmitting ? "Submitting…" : "Apply as a Vendor"}
          </button>
        </form>
      )}

      <h2 className="mt-14 text-xl font-bold text-slate-900">Frequently Asked Questions</h2>
      <div className="mt-4 divide-y divide-slate-200">
        {faqs.map((f) => (
          <div key={f.q} className="py-4">
            <p className="font-medium text-slate-900">{f.q}</p>
            <p className="mt-1 text-sm text-slate-600">{f.a}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
