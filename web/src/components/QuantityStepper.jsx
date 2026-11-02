import { FaMinus, FaPlus } from "react-icons/fa";

export default function QuantityStepper({ value, onChange, min = 1, max = 99, disabled = false, size = "md" }) {
  const btn = `flex items-center justify-center rounded-full border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:opacity-40 ${
    size === "sm" ? "h-7 w-7 text-[10px]" : "h-9 w-9 text-xs"
  }`;
  return (
    <div className="inline-flex items-center gap-3" onClick={(e) => e.stopPropagation()}>
      <button type="button" aria-label="Decrease quantity" disabled={disabled || value <= min} onClick={() => onChange(value - 1)} className={btn}>
        <FaMinus />
      </button>
      <span className="min-w-[1.5rem] text-center text-sm font-semibold tabular-nums text-slate-900" aria-live="polite">{value}</span>
      <button type="button" aria-label="Increase quantity" disabled={disabled || value >= max} onClick={() => onChange(value + 1)} className={btn}>
        <FaPlus />
      </button>
    </div>
  );
}
