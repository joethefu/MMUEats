import { useState } from "react";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { authService } from "../services/authService";

export default function ResendVerificationPage() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm();
  const [sent, setSent] = useState(false);

  const onSubmit = async ({ email }) => {
    try {
      await authService.resendVerification(email);
      setSent(true);
    } catch {
      toast.error("Could not resend right now. Please try again shortly.");
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-16 text-center sm:px-6">
      <h1 className="text-2xl font-bold text-slate-900">Resend verification email</h1>
      {sent ? (
        <p className="mt-4 text-slate-600">If an unverified account exists for that email, a new link is on its way.</p>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4 text-left" noValidate>
          <div>
            <label className="block text-sm font-medium text-slate-700">Email Address</label>
            <input
              type="email"
              {...register("email", { required: "Email is required" })}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            />
            {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {isSubmitting ? "Sending…" : "Resend Verification Email"}
          </button>
        </form>
      )}
    </div>
  );
}
