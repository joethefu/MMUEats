import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { FaPen, FaUserCircle, FaLock, FaChevronDown, FaSignOutAlt, FaCheckCircle, FaCamera } from "react-icons/fa";
import { useAuth } from "../contexts/AuthContext";
import { userService } from "../services/userService";
import { authService } from "../services/authService";
import Avatar from "../components/Avatar";
import PasswordInput from "../components/PasswordInput";
import LogoutConfirmModal from "../components/LogoutConfirmModal";
import ProfilePictureModal from "../components/ProfilePictureModal";
import { tokenStorage } from "../services/apiClient";

const inputCls = "mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none";

function apiError(err, fallback) {
  const e = err?.response?.data?.error;
  const details = e?.details && typeof e.details === "object" ? Object.values(e.details).flat().join(" ") : "";
  return details || e?.message || fallback;
}

function SettingsRow({ icon: Icon, title, subtitle, open, onToggle, children }) {
  return (
    <div>
      <button onClick={onToggle} className="flex w-full items-center gap-4 px-4 py-4 text-left hover:bg-slate-50" aria-expanded={open}>
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
          <Icon />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block font-medium text-slate-900">{title}</span>
          <span className="block truncate text-sm text-slate-500">{subtitle}</span>
        </span>
        <FaChevronDown className={`shrink-0 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`} size={12} />
      </button>
      {open && <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-5 sm:px-6">{children}</div>}
    </div>
  );
}

function PersonalInfo({ user, editing, setEditing, refreshUser }) {
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm({
    defaultValues: { full_name: user.full_name, phone_number: user.phone_number || "" },
  });

  const cancel = () => {
    reset({ full_name: user.full_name, phone_number: user.phone_number || "" });
    setEditing(false);
  };

  const onSubmit = async (values) => {
    try {
      await userService.updateMe(values);
      await refreshUser();
      toast.success("Profile updated");
      setEditing(false);
    } catch (err) {
      toast.error(apiError(err, "Couldn't update your profile."));
    }
  };

  if (!editing) {
    return (
      <>
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between gap-4"><dt className="text-slate-500">Name</dt><dd className="font-medium text-slate-900">{user.full_name}</dd></div>
          <div className="flex justify-between gap-4"><dt className="text-slate-500">Email</dt><dd className="break-all font-medium text-slate-900">{user.email}</dd></div>
          <div className="flex justify-between gap-4"><dt className="text-slate-500">Phone</dt><dd className="font-medium text-slate-900">{user.phone_number || "—"}</dd></div>
        </dl>
        <button onClick={() => setEditing(true)} className="mt-4 text-sm font-medium text-brand-600 hover:underline">Edit details</button>
      </>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <div>
        <label className="block text-sm font-medium text-slate-700">Full name</label>
        <input {...register("full_name", { required: "Name is required" })} className={inputCls} />
        {errors.full_name && <p className="mt-1 text-xs text-red-600">{errors.full_name.message}</p>}
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700">Email</label>
        <input value={user.email} disabled className={`${inputCls} bg-slate-100 text-slate-500`} />
        <p className="mt-1 text-xs text-slate-500">Email can't be changed here.</p>
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700">Phone number</label>
        <input {...register("phone_number", { required: "Phone number is required" })} className={inputCls} />
        {errors.phone_number && <p className="mt-1 text-xs text-red-600">{errors.phone_number.message}</p>}
      </div>
      <div className="flex gap-3">
        <button type="submit" disabled={isSubmitting} className="rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
          {isSubmitting ? "Saving…" : "Save changes"}
        </button>
        <button type="button" onClick={cancel} className="rounded-lg border border-slate-300 px-5 py-2 text-sm font-medium text-slate-700 hover:bg-white">Cancel</button>
      </div>
    </form>
  );
}

function SecurityPanel({ user, onPasswordChanged }) {
  const { register, handleSubmit, reset, watch, formState: { errors, isSubmitting } } = useForm();
  const newPassword = watch("new_password");

  const onSubmit = async (values) => {
    try {
      await authService.changePassword(values);
      reset();
      onPasswordChanged();
    } catch (err) {
      toast.error(apiError(err, "Couldn't change your password."));
    }
  };

  return (
    <div className="space-y-5">
      <ul className="space-y-2 text-sm text-slate-600">
        <li className="flex items-center gap-2">
          <FaCheckCircle className={user.is_email_verified ? "text-green-600" : "text-slate-300"} />
          {user.is_email_verified ? "Email address verified" : "Email address not verified"}
        </li>
        <li className="flex items-center gap-2"><FaCheckCircle className="text-green-600" /> Sessions are signed out when you log out</li>
      </ul>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <h3 className="text-sm font-semibold text-slate-900">Change password</h3>
        <div>
          <label className="block text-sm font-medium text-slate-700">Current password</label>
          <PasswordInput {...register("old_password", { required: "Enter your current password" })} />
          {errors.old_password && <p className="mt-1 text-xs text-red-600">{errors.old_password.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">New password</label>
          <PasswordInput {...register("new_password", { required: "Enter a new password", minLength: { value: 8, message: "At least 8 characters" } })} />
          {errors.new_password && <p className="mt-1 text-xs text-red-600">{errors.new_password.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Confirm new password</label>
          <PasswordInput {...register("confirm_password", { required: "Confirm your new password", validate: (v) => v === newPassword || "Passwords do not match" })} />
          {errors.confirm_password && <p className="mt-1 text-xs text-red-600">{errors.confirm_password.message}</p>}
        </div>
        <button type="submit" disabled={isSubmitting} className="rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
          {isSubmitting ? "Updating…" : "Update password"}
        </button>
      </form>
    </div>
  );
}

export default function ProfilePage() {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [section, setSection] = useState(null); // "personal" | "security" | null
  const [editing, setEditing] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const [pictureOpen, setPictureOpen] = useState(false);

  // All sessions are invalidated server-side after a password change: clear local state and ask for a fresh login.
  const onPasswordChanged = () => {
    toast.success("Password changed. Please log in again with your new password.", { duration: 6000 });
    // After re-login, go to the normal home rather than back to /profile (consumed by LoginPage).
    try { sessionStorage.setItem("mmueats_skip_return", "1"); } catch { /* ignore */ }
    navigate("/login", { replace: true });
    tokenStorage.clear();
    window.dispatchEvent(new Event("mmueats:logout"));
  };

  const toggle = (name) => {
    setSection((s) => (s === name ? null : name));
    setEditing(false);
  };

  const startEdit = () => {
    setSection("personal");
    setEditing(true);
  };

  const confirmLogout = async () => {
    setLoggingOut(true);
    // Leave the protected page first so the auth guard doesn't redirect to /login mid-logout.
    navigate("/", { replace: true });
    try {
      await logout();
      toast.success("You've been logged out");
    } catch {
      toast.error("Logged out locally, but the server couldn't be reached.");
    }
  };

  return (
    <div className="mx-auto max-w-xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-5">
        <button onClick={() => setPictureOpen(true)} aria-label="Change profile picture" className="group relative shrink-0 rounded-full">
          <Avatar user={user} size={64} />
          <span className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-brand-600 text-white group-hover:bg-brand-700">
            <FaCamera size={10} />
          </span>
        </button>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-lg font-bold text-slate-900">{user.full_name}</h1>
          <p className="truncate text-sm text-slate-500">{user.email}</p>
          {user.is_email_verified && (
            <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
              <FaCheckCircle size={10} /> Verified account
            </span>
          )}
        </div>
        <button onClick={startEdit} aria-label="Edit profile" className="self-start rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-brand-600">
          <FaPen size={14} />
        </button>
      </div>

      <h2 className="mb-2 mt-8 px-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Account settings</h2>
      <div className="divide-y divide-slate-100 overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <SettingsRow icon={FaUserCircle} title="Personal Information" subtitle="Name, email and phone number" open={section === "personal"} onToggle={() => toggle("personal")}>
          <PersonalInfo key={`${editing}-${user.full_name}-${user.phone_number}`} user={user} editing={editing} setEditing={setEditing} refreshUser={refreshUser} />
        </SettingsRow>
        <SettingsRow icon={FaLock} title="Security" subtitle="Password and account protection" open={section === "security"} onToggle={() => toggle("security")}>
          <SecurityPanel user={user} onPasswordChanged={onPasswordChanged} />
        </SettingsRow>
      </div>

      <hr className="my-6 border-slate-200" />
      <button onClick={() => setConfirmOpen(true)} className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left font-medium text-red-600 hover:bg-red-50">
        <FaSignOutAlt /> Log out
      </button>

      <ProfilePictureModal open={pictureOpen} user={user} onClose={() => setPictureOpen(false)} onUpdated={() => refreshUser()} />
      <LogoutConfirmModal open={confirmOpen} onCancel={() => setConfirmOpen(false)} onConfirm={confirmLogout} isLoading={loggingOut} />
    </div>
  );
}
