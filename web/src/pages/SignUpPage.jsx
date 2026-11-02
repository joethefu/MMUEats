import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { authService } from "../services/authService";
import PasswordInput from "../components/PasswordInput";

export default function SignUpPage() {
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm();
  const [submitted, setSubmitted] = useState(false);
  const navigate = useNavigate();
  const password = watch("password");

  const onSubmit = async (values) => {
    try {
      await authService.register({
        full_name: values.full_name,
        email: values.email,
        phone_number: values.phone_number,
        password: values.password,
        confirm_password: values.confirm_password,
      });
      setSubmitted(true);
      toast.success("Account created! Check your email to verify your address.");
    } catch (err) {
      const msg = err?.response?.data?.error?.message || "Something went wrong. Please try again.";
      toast.error(msg);
    }
  };

  if (submitted) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center px-4 py-24 text-center">
        <h1 className="text-2xl font-bold text-slate-900">Check your inbox</h1>
        <p className="mt-3 text-slate-600">
          We've sent a verification link to your email. Click it to activate your MMUEats account.
        </p>
        <Link to="/login" className="mt-6 text-sm font-medium text-brand-600 hover:underline">
          Back to Log in
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md px-4 py-16 sm:px-6">
      <h1 className="text-2xl font-bold text-slate-900">Create your MMUEats account</h1>
      <p className="mt-1 text-sm text-slate-600">Order food from campus vendors in minutes.</p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-4" noValidate>
        <div>
          <label className="block text-sm font-medium text-slate-700">Full Name</label>
          <input
            {...register("full_name", { required: "Full name is required" })}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            placeholder="Jane Wanjiru"
          />
          {errors.full_name && <p className="mt-1 text-xs text-red-600">{errors.full_name.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Email Address</label>
          <input
            type="email"
            {...register("email", {
              required: "Email is required",
              pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Enter a valid email address" },
            })}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            placeholder="you@gmail.com"
          />
          {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
          <p className="mt-1 text-xs text-slate-400">Any email provider works — a university email is not required.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Phone Number</label>
          <input
            {...register("phone_number", {
              required: "Phone number is required",
              pattern: { value: /^\+?[0-9]{9,15}$/, message: "Enter a valid phone number" },
            })}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            placeholder="+254712345678"
          />
          {errors.phone_number && <p className="mt-1 text-xs text-red-600">{errors.phone_number.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Password</label>
          <PasswordInput {...register("password", { required: "Password is required", minLength: { value: 8, message: "At least 8 characters" } })} />
          {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Confirm Password</label>
          <PasswordInput {...register("confirm_password", {
              required: "Please confirm your password",
              validate: (v) => v === password || "Passwords do not match",
            })} />
          {errors.confirm_password && <p className="mt-1 text-xs text-red-600">{errors.confirm_password.message}</p>}
        </div>

        <label className="flex items-start gap-2 text-sm text-slate-600">
          <input type="checkbox" {...register("terms", { required: "You must accept the Terms" })} className="mt-1" />
          I agree to the <Link to="/terms" className="text-brand-600 hover:underline">Terms and Conditions</Link>
        </label>
        {errors.terms && <p className="text-xs text-red-600">{errors.terms.message}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {isSubmitting ? "Creating account…" : "Create Account"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-600">
        Already have an account? <Link to="/login" className="font-medium text-brand-600 hover:underline">Log in</Link>
      </p>

      <div className="mt-10 rounded-xl border border-dashed border-slate-300 p-4 text-center">
        <p className="text-sm font-medium text-slate-700">Want to partner with MMUEats?</p>
        <p className="text-xs text-slate-500">Become a Vendor or Delivery Partner.</p>
        <Link to="/become-a-vendor" className="mt-2 inline-block text-xs font-semibold text-brand-600 hover:underline">
          Learn More →
        </Link>
      </div>
    </div>
  );
}
