import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { authService } from "../services/authService";

export default function ForgotPasswordPage() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm();
  const [sent, setSent] = useState(false);

  const onSubmit = async ({ email }) => {
    try {
      await authService.requestPasswordReset(email);
      setSent(true);
    } catch {
      toast.error("Something went wrong. Please try again.");
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-16 sm:px-6">
      <h1 className="text-2xl font-bold text-slate-900">Forgot your password?</h1>
      <p className="mt-1 text-sm text-slate-600">We'll email you a link to reset it.</p>

      {sent ? (
        <p className="mt-6 text-sm text-slate-600">
          If an account exists for that email, a reset link has been sent. It expires in 1 hour.
        </p>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-4" noValidate>
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
            {isSubmitting ? "Sending…" : "Send Reset Link"}
          </button>
        </form>
      )}

      <p className="mt-6 text-center text-sm text-slate-600">
        <Link to="/login" className="font-medium text-brand-600 hover:underline">Back to Log in</Link>
      </p>
    </div>
  );
}
