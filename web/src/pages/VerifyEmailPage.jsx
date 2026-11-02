import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { authService } from "../services/authService";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState("verifying"); // verifying | success | expired | error

  useEffect(() => {
    if (!token) {
      setStatus("error");
      return;
    }
    authService
      .verifyEmail(token)
      .then(() => setStatus("success"))
      .catch((err) => {
        const code = err?.response?.data?.error?.code;
        setStatus(code === "token_expired" ? "expired" : "error");
      });
  }, [token]);

  return (
    <div className="mx-auto flex max-w-md flex-col items-center px-4 py-24 text-center">
      {status === "verifying" && <p className="text-slate-600">Verifying your email…</p>}

      {status === "success" && (
        <>
          <h1 className="text-2xl font-bold text-slate-900">Email verified 🎉</h1>
          <p className="mt-3 text-slate-600">Your account is now active. You can log in.</p>
          <Link to="/login" className="mt-6 rounded-lg bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
            Go to Login
          </Link>
        </>
      )}

      {status === "expired" && (
        <>
          <h1 className="text-2xl font-bold text-slate-900">Link expired</h1>
          <p className="mt-3 text-slate-600">This verification link has expired. Request a new one to continue.</p>
          <Link to="/resend-verification" className="mt-6 text-sm font-medium text-brand-600 hover:underline">
            Resend Verification Email
          </Link>
        </>
      )}

      {status === "error" && (
        <>
          <h1 className="text-2xl font-bold text-slate-900">Verification failed</h1>
          <p className="mt-3 text-slate-600">This link is invalid or has already been used.</p>
          <Link to="/resend-verification" className="mt-6 text-sm font-medium text-brand-600 hover:underline">
            Resend Verification Email
          </Link>
        </>
      )}
    </div>
  );
}
