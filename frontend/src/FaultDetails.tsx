import type { FaultAnalysis } from "./api";
import { formatDuration, formatFrequency, formatPercent } from "./format";

const change = new Intl.NumberFormat(undefined, { signDisplay: "exceptZero", maximumFractionDigits: 2 });

export default function FaultDetails({ analysis, availability }: { analysis: FaultAnalysis; availability: number }) {
  const { comparison } = analysis;
  const metrics = [
    ["Fault duration", formatDuration(analysis.duration_seconds)],
    ["Maximum measurement error", formatFrequency(analysis.max_measurement_error_hz)],
    ["Breaker operations", analysis.breaker_operations],
    ["Load disconnected", formatDuration(analysis.load_disconnected_seconds)],
    ["Actual frequency violating samples", analysis.actual_frequency_violation_count],
  ];
  const rows = [
    ["Breaker operations", analysis.breaker_operations, comparison.normal_breaker_operations,
      change.format(comparison.breaker_operations_delta)],
    ["Load connection availability", formatPercent(availability),
      formatPercent(comparison.normal_load_connection_availability_pct),
      `${change.format(comparison.load_connection_availability_delta_pp)} pp`],
  ];

  return (
    <section aria-label="FS101 fault summary" className="mt-3 space-y-3">
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {metrics.map(([label, value]) => (
          <div key={label}>
            <dt className="text-sm text-slate-600">{label}</dt>
            <dd className="font-medium tabular-nums">{value}</dd>
          </div>
        ))}
      </dl>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <caption className="border-t border-slate-200 pt-3 text-left font-semibold">Normal Baseline Comparison</caption>
          <thead className="text-slate-600">
            <tr>
              <th scope="col" className="py-2 text-left font-medium">Metric</th>
              <th scope="col" className="py-2 pl-3 text-right font-medium">Fault Run</th>
              <th scope="col" className="py-2 pl-3 text-right font-medium">Normal Run</th>
              <th scope="col" className="py-2 pl-3 text-right font-medium">Change</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map(([label, fault, normal, difference]) => (
              <tr key={label}>
                <th scope="row" className="py-2 text-left font-medium">{label}</th>
                <td className="py-2 pl-3 text-right tabular-nums">{fault}</td>
                <td className="py-2 pl-3 text-right tabular-nums">{normal}</td>
                <td className="py-2 pl-3 text-right tabular-nums">{difference}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
