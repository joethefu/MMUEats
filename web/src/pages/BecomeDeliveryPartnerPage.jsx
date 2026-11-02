import { useState } from "react";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import apiClient from "../services/apiClient";

const faqs = [
  { q: "Do I need my own bicycle or motorbike?", a: "Yes, you'll need reliable transportation suited to campus and nearby routes." },
  { q: "How and when do I get paid?", a: "Earnings are tracked per delivery and paid out on a regular schedule via M-Pesa." },
  { q: "Can I choose my working hours?", a: "Yes — toggle Online/Offline whenever you're available to accept deliveries." },
];

export default function BecomeDeliveryPartnerPage() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm();
  const [submitted, setSubmitted] = useState(false);

  const onSubmit = async (values) => {
    try {
      await apiClient.post("/users/delivery-partner-applications/", values);
      setSubmitted(true);
      toast.success("Application submitted!");
    } catch {
      toast.error("Could not submit your application. Please try again.");
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold text-slate-900">Become a Delivery Partner</h1>
      <p className="mt-3 text-slate-600">
        Earn flexible income delivering food across MMU campus and nearby locations. Set your own hours,
        accept the deliveries that work for you, and get paid for every completed trip.
      </p>

      <div className="mt-10 grid gap-8 sm:grid-cols-2">
        <div>
          <h2 className="font-semibold text-slate-900">What a Delivery Partner does</h2>
          <p className="mt-2 text-sm text-slate-600">
            Pick up orders from vendors and deliver them to customers at hostels and other approved campus locations.
          </p>
        </div>
        <div>
          <h2 className="font-semibold text-slate-900">Requirements</h2>
          <ul className="mt-2 list-disc pl-5 text-sm text-slate-600 space-y-1">
            <li>Valid means of transport (bicycle, motorbike, or on foot for nearby routes)</li>
            <li>A smartphone with data access</li>
            <li>Reliable availability during your chosen hours</li>
          </ul>
        </div>
        <div>
          <h2 className="font-semibold text-slate-900">Safety requirements</h2>
          <p className="mt-2 text-sm text-slate-600">
            Follow all traffic rules, wear high-visibility gear where applicable, and report any safety
            concerns immediately through the app.
          </p>
        </div>
        <div>
          <h2 className="font-semibold text-slate-900">Availability</h2>
          <p className="mt-2 text-sm text-slate-600">
            Go online whenever you want to accept deliveries — there are no fixed shifts.
          </p>
        </div>
      </div>

      <h2 className="mt-12 text-xl font-bold text-slate-900">Apply as a Delivery Partner</h2>

      {submitted ? (
        <p className="mt-4 rounded-lg bg-green-50 border border-green-200 p-4 text-sm text-green-800">
          Thanks! We've received your application and will email you once it's reviewed.
        </p>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700">Full Name</label>
              <input {...register("full_name", { required: true })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
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
              <label className="block text-sm font-medium text-slate-700">Preferred Delivery Area</label>
              <input {...register("preferred_area", { required: true })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Availability</label>
            <input placeholder="e.g. Weekday evenings, weekends" {...register("availability")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <button type="submit" disabled={isSubmitting} className="rounded-lg bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
            {isSubmitting ? "Submitting…" : "Apply as a Delivery Partner"}
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
