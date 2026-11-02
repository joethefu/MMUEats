import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { authService } from "../services/authService";
import PasswordInput from "../components/PasswordInput";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm();
  const [done, setDone] = useState(false);
  const navigate = useNavigate();
  const password = watch("password");

  const onSubmit = async (values) => {
    try {
      await authService.confirmPasswordReset({ token, password: values.password, confirm_password: values.confirm_password });
      setDone(true);
      toast.success("Password reset. You can log in now.");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      const code = err?.response?.data?.error?.code;
      toast.error(code === "token_expired" ? "This link has expired. Request a new one." : "Reset failed. The link may be invalid.");
    }
  };

  if (!token) {
    return (
      <div className="mx-auto max-w-md px-4 py-24 text-center">
        <p className="text-slate-600">Missing reset token.</p>
        <Link to="/forgot-password" className="mt-4 inline-block text-sm font-medium text-brand-600 hover:underline">
          Request a new link
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md px-4 py-16 sm:px-6">
      <h1 className="text-2xl font-bold text-slate-900">Set a new password</h1>
      {done ? (
        <p className="mt-6 text-sm text-slate-600">Redirecting you to log in…</p>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-4" noValidate>
          <div>
            <label className="block text-sm font-medium text-slate-700">New Password</label>
            <PasswordInput {...register("password", { required: "Password is required", minLength: { value: 8, message: "At least 8 characters" } })} />
            {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Confirm New Password</label>
            <PasswordInput {...register("confirm_password", {
                required: "Please confirm your password",
                validate: (v) => v === password || "Passwords do not match",
              })} />
            {errors.confirm_password && <p className="mt-1 text-xs text-red-600">{errors.confirm_password.message}</p>}
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {isSubmitting ? "Saving…" : "Reset Password"}
          </button>
        </form>
      )}
    </div>
  );
}
