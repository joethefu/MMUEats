import { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";
import { vendorService } from "../../services/vendorService";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

export default function VendorReportsPage() {
  const [report, setReport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    vendorService.getSalesReport().then(setReport).finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <p className="text-slate-500">Loading reports…</p>;
  if (!report) return <p className="text-slate-500">Set up your restaurant profile first.</p>;

  const chartData = {
    labels: report.daily_sales.map((d) => d.day),
    datasets: [
      {
        label: "Revenue (KES)",
        data: report.daily_sales.map((d) => d.revenue),
        borderColor: "#b8202e",
        backgroundColor: "rgba(184,32,46,0.1)",
        tension: 0.3,
      },
    ],
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Sales Reports</h1>
      <p className="mt-1 text-sm text-slate-500">{report.start_date} – {report.end_date}</p>

      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Total Revenue</p>
          <p className="mt-1 text-xl font-bold text-slate-900">KES {report.total_revenue}</p>
        </div>
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Total Orders</p>
          <p className="mt-1 text-xl font-bold text-slate-900">{report.total_orders}</p>
        </div>
      </div>

      {report.daily_sales.length > 0 ? (
        <div className="mt-8 rounded-xl border border-slate-200 p-4">
          <Line data={chartData} />
        </div>
      ) : (
        <p className="mt-8 text-sm text-slate-500">No delivered orders in this period yet.</p>
      )}

      <div className="mt-8 rounded-xl border border-slate-200 p-4">
        <h2 className="font-semibold text-slate-900">Meal Performance</h2>
        {report.meal_performance.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">No meal sales yet.</p>
        ) : (
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="pb-2">Meal</th>
                <th className="pb-2">Orders</th>
                <th className="pb-2">Rating</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {report.meal_performance.map((m) => (
                <tr key={m.id}>
                  <td className="py-2">{m.name}</td>
                  <td className="py-2">{m.order_count}</td>
                  <td className="py-2">{m.average_rating || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
