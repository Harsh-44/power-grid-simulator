import type { SimulationResult } from "./api";
import FaultDetails from "./FaultDetails";
import { formatDuration, formatFrequency, formatFrequencyNumber, formatPercent } from "./format";
import RunDiagnostics from "./RunDiagnostics";

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <dt className="text-sm text-slate-600">{label}</dt>
      <dd className="font-medium tabular-nums">{value}</dd>
    </div>
  );
}

export default function RunDetails({
  result,
  onSeek,
}: {
  result: SimulationResult;
  onSeek: (time: number) => void;
}) {
  const { config, summary: { frequency, load, generator, breaker } } = result;
  return (
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4 text-[13px]">
      {result.fault_analysis && (
        <details open className="border-b border-slate-200 pb-3">
          <summary className="cursor-pointer font-semibold">Fault analysis and baseline</summary>
          <FaultDetails analysis={result.fault_analysis} availability={load.connection_availability_pct} />
        </details>
      )}
      <details open={!result.fault_analysis}>
        <summary className="cursor-pointer font-semibold">Operational metrics</summary>
        <div className="mt-3 grid gap-3 text-[13px] sm:grid-cols-2">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <h3 className="mb-2 font-semibold">Frequency and safety</h3>
            <dl className="space-y-2">
              <Metric label="Actual range" value={`${formatFrequencyNumber(frequency.min_actual_frequency_hz)}–${formatFrequency(frequency.max_actual_frequency_hz)}`} />
              <Metric label="Safe band" value={`${formatFrequencyNumber(config.lower_limit_hz)}–${formatFrequency(config.upper_limit_hz)}`} />
              <Metric label="Unsafe frequency samples" value={frequency.violating_sample_count} />
              <Metric label="Violation episodes" value={frequency.violation_episode_count} />
              <Metric label="Average actual frequency" value={formatFrequency(frequency.average_actual_frequency_hz)} />
              <Metric label="Time within limits" value={formatDuration(frequency.within_limits_seconds)} />
              <Metric label="Time outside limits" value={formatDuration(frequency.outside_limits_seconds)} />
              <Metric label="CB101 closed below lower limit" value={formatDuration(frequency.closed_below_limit_seconds)} />
              <Metric label="Under-frequency" value={`${frequency.under_frequency_sample_count} samples · ${frequency.under_frequency_episode_count} episodes`} />
              <Metric label="Over-frequency" value={`${frequency.over_frequency_sample_count} samples · ${frequency.over_frequency_episode_count} episodes`} />
              <Metric label="Minimum margin" value={formatFrequency(frequency.minimum_margin_hz)} />
            </dl>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <h3 className="mb-2 font-semibold">L101 station load</h3>
            <dl className="space-y-2">
              <Metric label="Connection availability" value={formatPercent(load.connection_availability_pct)} />
              <Metric label="Connected" value={formatDuration(load.connected_seconds)} />
              <Metric label="Disconnected" value={formatDuration(load.disconnected_seconds)} />
              <Metric label="Longest disconnection" value={formatDuration(load.longest_disconnection_seconds)} />
              <Metric label="Powered by G101" value={formatDuration(load.powered_seconds)} />
              <Metric label="Connected without generator power" value={formatDuration(load.connected_without_generator_power_seconds)} />
              <Metric label="Disconnection episodes" value={load.disconnection_episodes} />
              <Metric label="Average disconnection" value={formatDuration(load.average_disconnection_seconds)} />
            </dl>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <h3 className="mb-2 font-semibold">G101 generator</h3>
            <dl className="space-y-2">
              <Metric label="OFF" value={formatDuration(generator.off_seconds)} />
              <Metric label="ON" value={formatDuration(generator.on_seconds)} />
              <Metric label="Share of time ON" value={formatPercent(generator.on_pct)} />
              <Metric label="State transitions" value={generator.state_transitions} />
              <Metric label="ON with breaker open" value={formatDuration(generator.on_while_breaker_open_seconds)} />
            </dl>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <h3 className="mb-2 font-semibold">CB101 breaker</h3>
            <dl className="space-y-2">
              <Metric label="Total switching operations" value={breaker.switching_operations} />
              <Metric label="CLOSED" value={formatDuration(breaker.closed_seconds)} />
              <Metric label="OPEN" value={formatDuration(breaker.open_seconds)} />
              <Metric label="Open / close operations" value={`${breaker.open_operations} / ${breaker.close_operations}`} />
              <Metric label="Continuous open intervals" value={breaker.open_intervals} />
              <Metric label="Longest open interval" value={formatDuration(breaker.longest_open_interval_seconds)} />
            </dl>
          </div>
        </div>
      </details>
      <RunDiagnostics result={result} onSeek={onSeek} />
    </section>
  );
}

