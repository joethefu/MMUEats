import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { useAuth } from "../contexts/AuthContext";
import StarRating from "./StarRating";
import Avatar from "./Avatar";

/** Shared reviews list + form for vendors and meals. `api` = { list(id), submit({rating, comment}) }. */
export default function ReviewsSection({ targetId, api, onChanged, title = "Ratings & reviews" }) {
  const { user } = useAuth();
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);
  const touched = useRef(false); // true once the user edits the form, so a late-loading saved review can't overwrite their typing

  const load = () =>
    api.list(targetId).then((d) => setReviews(d.results || d || [])).finally(() => setLoading(false));

  useEffect(() => {
    setLoading(true);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetId]);

  const mine = user ? reviews.find((r) => r.customer === user.id) : null;
  useEffect(() => {
    touched.current = false;
    setRating(0);
    setComment("");
  }, [targetId]);
  useEffect(() => {
    if (mine && !touched.current) {
      setRating(mine.rating);
      setComment(mine.comment || "");
    }
  }, [mine?.id, mine?.rating, mine?.comment]); // eslint-disable-line react-hooks/exhaustive-deps

  const submit = async (e) => {
    e.preventDefault();
    if (!rating) return toast.error("Choose a star rating first.");
    setSaving(true);
    try {
      await api.submit({ rating, comment: comment.trim() });
      toast.success(mine ? "Review updated" : "Thanks for your review!");
      touched.current = false; // let the saved version repopulate the form
      await load();
      onChanged?.();
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || "Couldn't save your review.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="mt-10">
      <h2 className="text-lg font-bold text-slate-900">{title}</h2>

      {user?.role === "customer" ? (
        <form onSubmit={submit} className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-sm font-medium text-slate-700">{mine ? "Your review" : "Rate this"}</p>
          <div className="mt-1"><StarRating value={rating} onChange={(n) => { touched.current = true; setRating(n); }} size={24} /></div>
          <textarea
            value={comment}
            onChange={(e) => { touched.current = true; setComment(e.target.value); }}
            rows={3}
            maxLength={1000}
            placeholder="Write a review (optional)"
            className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          />
          <button disabled={saving} className="mt-3 rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
            {saving ? "Saving…" : mine ? "Update review" : "Submit review"}
          </button>
        </form>
      ) : (
        !user && <p className="mt-3 text-sm text-slate-500">Log in as a customer to leave a review.</p>
      )}

      <div className="mt-6 space-y-4">
        {loading && <p className="text-sm text-slate-500">Loading reviews…</p>}
        {!loading && reviews.length === 0 && <p className="text-sm text-slate-500">No reviews yet. Be the first!</p>}
        {reviews.map((r) => (
          <div key={r.id} className="flex gap-3">
            <Avatar user={{ full_name: r.customer_name, profile_picture: r.customer_picture }} size={36} />
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-900">
                {r.customer_name} <span className="ml-2 text-xs font-normal text-slate-400">{new Date(r.created_at).toLocaleDateString()}</span>
              </p>
              <StarRating value={r.rating} size={13} />
              {r.comment && <p className="mt-1 whitespace-pre-line text-sm text-slate-600">{r.comment}</p>}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
