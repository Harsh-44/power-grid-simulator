import type { SimulationResult } from "./api";
import { configuredScenario, scenarioLabels } from "./api";
import { formatDuration } from "./format";

export default function RunOverview({ result, running, pending, onDetails }: {
  result: SimulationResult;
  running: boolean;
  pending: boolean;
  onDetails: () => void;
}) {
  const { config, summary: { frequency, load } } = result;
  const unsafe = frequency.violating_sample_count;

  return (
    <section aria-label="Run overview" className="flex flex-wrap items-center gap-x-3 gap-y-2 px-4 py-3">
      <span role="status" className={[
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold",
        running ? "bg-blue-50 text-blue-800" : "bg-slate-100 text-slate-700",
      ].join(" ")}>
        <span aria-hidden="true" className={"size-1.5 rounded-full " + (running ? "bg-blue-600" : "bg-slate-500")} />
        {running ? "Running simulation…" : "Run complete"}
      </span>
      <span className="text-[13px] text-slate-600 tabular-nums">
        {(pending || running) && "Showing "}
        {scenarioLabels[configuredScenario(config)]} · {formatDuration(config.duration_seconds)}
      </span>
      {!running && pending && (
        <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-900" title="Run Simulation to apply edited settings">
          Pending settings
        </span>
      )}
      <div className="flex flex-wrap items-center gap-2 sm:ml-auto">
        {config.manual_state_testing && (
          <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-900">Automatic control off</span>
        )}
        {load.connected_without_generator_power_seconds > 0 && (
          <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-900">Connected without generator power</span>
        )}
        <span className={[
          "rounded-full px-2.5 py-1 text-xs font-semibold tabular-nums",
          unsafe ? "bg-red-100 text-red-900" : "bg-emerald-50 text-emerald-800",
        ].join(" ")}>
          {unsafe ? unsafe + (unsafe === 1 ? " unsafe frequency sample" : " unsafe frequency samples") : "Run within frequency limits"}
        </span>
        <button
          type="button"
          aria-haspopup="dialog"
          onClick={onDetails}
          className="h-8 rounded-md border border-slate-300 px-2.5 text-[13px] font-semibold whitespace-nowrap text-blue-800 transition-colors hover:border-blue-300 hover:bg-blue-50"
        >
          Run details
        </button>
      </div>
    </section>
  );
}
