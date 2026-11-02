import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FaSearch, FaTimes } from "react-icons/fa";
import { mealService } from "../services/restaurantService";

/** Navbar search over available menu items, with a live suggestions dropdown. */
export default function SearchBar({ className = "" }) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const ref = useRef(null);
  const navigate = useNavigate();
  const term = q.trim();

  useEffect(() => {
    if (term.length < 2) {
      setResults([]);
      setLoading(false);
      return undefined;
    }
    setLoading(true);
    let cancelled = false;
    const t = setTimeout(() => {
      mealService
        .list({ search: term })
        .then((d) => !cancelled && setResults((d.results || []).slice(0, 6)))
        .catch(() => !cancelled && setResults([]))
        .finally(() => !cancelled && setLoading(false));
    }, 250);
    return () => { cancelled = true; clearTimeout(t); };
  }, [term]);

  useEffect(() => {
    const away = (e) => ref.current && !ref.current.contains(e.target) && setOpen(false);
    document.addEventListener("mousedown", away);
    return () => document.removeEventListener("mousedown", away);
  }, []);

  const submit = (e) => {
    e.preventDefault();
    if (!term) return;
    setOpen(false);
    navigate(`/restaurants?q=${encodeURIComponent(term)}`);
  };

  return (
    <div ref={ref} className={`relative ${className}`}>
      <form onSubmit={submit} role="search" className="relative">
        <FaSearch className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={13} />
        <input
          type="search"
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          placeholder="Search food…"
          aria-label="Search menu items"
          className="h-9 w-full rounded-full border border-slate-300 bg-slate-50 pl-9 pr-8 text-sm focus:border-brand-500 focus:bg-white focus:outline-none [&::-webkit-search-cancel-button]:hidden"
        />
        {q && (
          <button type="button" aria-label="Clear search" onClick={() => { setQ(""); setResults([]); }} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
            <FaTimes size={12} />
          </button>
        )}
      </form>

      {open && term.length >= 2 && (
        <div className="absolute left-0 right-0 z-50 mt-2 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
          {loading && results.length === 0 && <p className="p-3 text-sm text-slate-500">Searching…</p>}
          {!loading && results.length === 0 && <p className="p-3 text-sm text-slate-500">No food matches “{term}”.</p>}
          {results.map((m) => (
            <Link key={m.id} to={`/meals/${m.id}`} onClick={() => setOpen(false)} className="flex items-center gap-3 px-3 py-2 hover:bg-slate-50">
              <span className="h-10 w-10 shrink-0 overflow-hidden rounded-lg bg-slate-100">
                {m.image && <img src={m.image} alt="" className="h-full w-full object-cover" />}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium text-slate-900">{m.name}</span>
                <span className="block truncate text-xs text-slate-500">{m.restaurant_name}</span>
              </span>
              <span className="text-sm font-semibold text-brand-600">KES {m.discounted_price}</span>
            </Link>
          ))}
          {results.length > 0 && (
            <button onClick={submit} className="block w-full border-t border-slate-100 px-3 py-2 text-left text-sm font-medium text-brand-600 hover:bg-slate-50">
              See all results for “{term}”
            </button>
          )}
        </div>
      )}
    </div>
  );
}
