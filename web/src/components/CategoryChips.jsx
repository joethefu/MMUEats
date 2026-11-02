/** Compact rounded category buttons in one horizontally scrollable row, with an "All" option. */
export default function CategoryChips({ categories, selected, onSelect }) {
  const items = [{ id: "", name: "All" }, ...categories];
  return (
    <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
      <div role="tablist" aria-label="Food categories" className="no-scrollbar -mx-1 flex gap-2 overflow-x-auto px-1 py-3">
        {items.map((c) => {
          const active = String(selected) === String(c.id);
          return (
            <button
              key={c.id || "all"}
              role="tab"
              aria-selected={active}
              onClick={() => onSelect(c.id)}
              className={`shrink-0 whitespace-nowrap rounded-full border px-4 py-1.5 text-sm font-medium transition ${
                active ? "border-brand-600 bg-brand-600 text-white" : "border-slate-200 bg-white text-slate-700 hover:border-brand-400 hover:text-brand-600"
              }`}
            >
              {c.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}
