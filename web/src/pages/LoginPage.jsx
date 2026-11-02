import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { useAuth } from "../contexts/AuthContext";
import { authService } from "../services/authService";
import PasswordInput from "../components/PasswordInput";

const UNVERIFIED_CODE = "email_not_verified";

export default function LoginPage() {
  const { register, handleSubmit, getValues, formState: { errors, isSubmitting } } = useForm();
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [needsVerification, setNeedsVerification] = useState(false);
  const [resending, setResending] = useState(false);

  const onSubmit = async (values) => {
    setNeedsVerification(false);
    try {
      const user = await login(values);
      toast.success(`Welcome back, ${user.full_name.split(" ")[0]}!`);
      const roleHome = { vendor: "/vendor/dashboard", delivery_partner: "/delivery/dashboard", admin: "/admin/dashboard" };
      let skipReturn = false;
      try {
        skipReturn = sessionStorage.getItem("mmueats_skip_return") === "1";
        sessionStorage.removeItem("mmueats_skip_return");
      } catch { /* ignore */ }
      const redirectTo = (!skipReturn && location.state?.from?.pathname) || roleHome[user.role] || "/restaurants";
      navigate(redirectTo, { replace: true });
    } catch (err) {
      const code = err?.response?.data?.error?.code;
      const message = err?.response?.data?.error?.message;
      if (code === UNVERIFIED_CODE) {
        setNeedsVerification(true);
      } else {
        toast.error(message || "Invalid email or password.");
      }
    }
  };

  const handleResend = async () => {
    setResending(true);
    try {
      await authService.resendVerification(getValues("email"));
      toast.success("Verification email sent — check your inbox.");
    } catch {
      toast.error("Could not resend right now. Please try again shortly.");
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-16 sm:px-6">
      <h1 className="text-2xl font-bold text-slate-900">Log in to MMUEats</h1>

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

        <div>
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-slate-700">Password</label>
            <Link to="/forgot-password" className="text-xs font-medium text-brand-600 hover:underline">Forgot password?</Link>
          </div>
          <PasswordInput {...register("password", { required: "Password is required" })} />
          {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>}
        </div>

        {needsVerification && (
          <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-sm text-amber-800">
            Please verify your email address before logging in.
            <button
              type="button"
              onClick={handleResend}
              disabled={resending}
              className="ml-1 font-semibold underline disabled:opacity-60"
            >
              {resending ? "Sending…" : "Resend Verification Email"}
            </button>
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {isSubmitting ? "Logging in…" : "Log in"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-600">
        Don't have an account? <Link to="/signup" className="font-medium text-brand-600 hover:underline">Sign up</Link>
      </p>
    </div>
  );
}
