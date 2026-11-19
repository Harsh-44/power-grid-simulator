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
  const pendingSettings = !running && pending;
  const connectedWithoutPower = load.connected_without_generator_power_seconds > 0;

  return (
    <section aria-label="Run overview" className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-2 gap-y-2.5 px-4 py-3">
      <p className="text-[13px] font-semibold text-slate-700 tabular-nums">
        {(pending || running) && "Showing "}
        {scenarioLabels[configuredScenario(config)]} · {formatDuration(config.duration_seconds)}
      </p>
      <span role="status" className={[
        "inline-flex items-center gap-1.5 justify-self-end rounded-full px-2.5 py-1 text-xs font-semibold",
        running ? "bg-blue-50 text-blue-800" : "bg-slate-100 text-slate-700",
      ].join(" ")}>
        <span aria-hidden="true" className={"size-1.5 shrink-0 rounded-full " + (running ? "bg-blue-600" : "bg-slate-500")} />
        {running ? "Running simulation…" : "Run complete"}
      </span>
      <span className={[
        "justify-self-start rounded-full px-2.5 py-1 text-xs font-semibold tabular-nums",
        unsafe ? "bg-red-100 text-red-900" : "bg-emerald-50 text-emerald-800",
      ].join(" ")}>
        {unsafe ? unsafe + (unsafe === 1 ? " unsafe frequency sample" : " unsafe frequency samples") : "Run within frequency limits"}
      </span>
      <button
        type="button"
        aria-haspopup="dialog"
        onClick={onDetails}
        className="h-8 cursor-pointer justify-self-end rounded-md border border-blue-200 bg-blue-50 px-2.5 text-[13px] font-semibold whitespace-nowrap text-blue-800 transition-colors hover:border-blue-300 hover:bg-blue-100 focus-visible:outline-offset-0"
      >
        Run details
      </button>
      {(pendingSettings || config.manual_state_testing || connectedWithoutPower) && (
        <div className="col-span-2 flex flex-wrap gap-2">
          {pendingSettings && (
            <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-900" title="Run Simulation to apply edited settings">
              Pending settings
            </span>
          )}
          {config.manual_state_testing && (
            <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-900">Automatic control off</span>
          )}
          {connectedWithoutPower && (
            <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-900">Connected without generator power</span>
          )}
        </div>
      )}
    </section>
  );
}
