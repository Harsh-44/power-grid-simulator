import type { SimulationSample } from "./api";
import { formatFrequency, frequencyConditions } from "./format";

export default function StateInspector({ sample, activeFault }: {
  sample: Readonly<SimulationSample>;
  activeFault: boolean;
}) {
  const unsafe = sample.frequency_condition !== "normal";
  return (
    <section className="space-y-3 p-4">
      <h2 className="shrink-0 text-[13px] font-semibold">Selected state</h2>
      <dl className="grid min-w-0 grid-cols-2 gap-y-3 text-sm">
        <div className="col-span-2 min-w-0">
          <dt className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs font-medium text-slate-600">
            <span>FS101 · Frequency</span>
            <span className={`rounded-full px-2 py-0.5 text-[11px] leading-none font-semibold ${unsafe ? "bg-red-100 text-red-800" : "bg-emerald-50 text-emerald-800"}`}>
              {frequencyConditions[sample.frequency_condition]}
            </span>
            {activeFault && <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] leading-none font-semibold text-amber-900">FS101 bias active</span>}
          </dt>
          <dd className="mt-0.5 flex flex-wrap gap-x-3 gap-y-0.5 text-[13px] text-slate-600 tabular-nums">
            <span title={`${sample.actual_frequency_hz} Hz`}>Actual <strong className="text-slate-900">{formatFrequency(sample.actual_frequency_hz)}</strong></span>
            <span title={`${sample.reported_frequency_hz} Hz`}>Reported <strong className="text-slate-900">{formatFrequency(sample.reported_frequency_hz)}</strong></span>
          </dd>
        </div>
        <div className="min-w-0">
          <dt className="text-xs font-medium text-slate-600">G101 · Generator</dt>
          <dd className="mt-0.5">
            <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${sample.generator_state === "ON" ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-slate-700"}`}>
              {sample.generator_state}
            </span>
          </dd>
        </div>
        <div className="min-w-0 border-l border-slate-200 pl-3">
          <dt className="text-xs font-medium text-slate-600">CB101 · Breaker</dt>
          <dd className="mt-0.5"><span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">{sample.breaker_state}</span></dd>
        </div>
        <div className="col-span-2 min-w-0 border-t border-slate-200 pt-2">
          <dt className="text-xs font-medium text-slate-600">L101 · Station load</dt>
          <dd className="mt-0.5 flex flex-wrap items-baseline gap-x-2 gap-y-0.5 text-[13px]">
            <span className="font-semibold">{sample.load_connected ? "Connected" : "Disconnected"}</span>
            <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${sample.load_powered ? "bg-emerald-50 text-emerald-800" : "bg-amber-100 text-amber-900"}`}>
              {sample.load_powered ? "Powered by G101" : "Unpowered"}
            </span>
          </dd>
        </div>
      </dl>
    </section>
  );
}
