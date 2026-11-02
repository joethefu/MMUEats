export default function SimplePage({ title, children }) {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
      <div className="prose prose-slate mt-4 max-w-none text-slate-600">{children}</div>
    </div>
  );
}
