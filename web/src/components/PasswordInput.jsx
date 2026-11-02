import { useState } from "react";
import { FaEye, FaEyeSlash } from "react-icons/fa";

/**
 * Password field with a show/hide "eye" toggle.
 * Drop-in for <input type="password" {...register("password")} />
 */
export default function PasswordInput({ className = "", ...props }) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="relative mt-1">
      <input
        {...props}
        type={visible ? "text" : "password"}
        className={`w-full rounded-lg border border-slate-300 px-3 py-2 pr-10 text-sm focus:border-brand-500 focus:outline-none ${className}`}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? "Hide password" : "Show password"}
        className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-400 hover:text-slate-600"
        tabIndex={-1}
      >
        {visible ? <FaEyeSlash /> : <FaEye />}
      </button>
    </div>
  );
}
