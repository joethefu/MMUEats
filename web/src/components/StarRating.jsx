import { useState } from "react";
import { FaStar } from "react-icons/fa";

/** Read-only stars (value may be fractional) or, with onChange, an interactive 1-5 picker. */
export default function StarRating({ value = 0, onChange, size = 16 }) {
  const [hover, setHover] = useState(0);
  const shown = hover || value;
  return (
    <span className="inline-flex items-center gap-0.5" role={onChange ? "radiogroup" : "img"} aria-label={`${Number(value) || 0} out of 5 stars`}>
      {[1, 2, 3, 4, 5].map((n) => {
        const filled = shown >= n - 0.25;
        const star = <FaStar size={size} className={filled ? "text-gold-500" : "text-slate-300"} />;
        return onChange ? (
          <button
            key={n}
            type="button"
            role="radio"
            aria-checked={value === n}
            aria-label={`${n} star${n > 1 ? "s" : ""}`}
            onMouseEnter={() => setHover(n)}
            onMouseLeave={() => setHover(0)}
            onClick={() => onChange(n)}
            className="p-0.5"
          >
            {star}
          </button>
        ) : (
          <span key={n}>{star}</span>
        );
      })}
    </span>
  );
}
